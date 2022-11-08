"""
HTTP repository implementation.

This module implements a subclass of the `generic_repository.repository.Repository`
class with http actions.
"""
import cgi
from http import HTTPStatus
from typing import Any, Dict, List, Optional, cast

import httpx  # pylint: disable=import-error

from .exceptions import InvalidPayloadException, ItemNotFoundException
from .mapper import LambdaMapper, Mapper
from .repository import Repository


class HttpRepository(Repository[str, Any, Any, Any, Any]):
    """An http repository.

    To use it, you must provide an httpx async client.

    For example:
    >>> import asyncio
    >>> from httpx import AsyncClient
    >>> client = AsyncClient(base_url='https://jsonplaceholder.typicode.com')
    >>> repo = HttpRepository(client, base_url='/posts')
    >>> repo
    <generic_repository.http.HttpRepository object at ...>
    >>>
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None,
        count_mapper: Optional[Mapper[Any, int]] = None,
        list_mapper: Optional[Mapper[Any, List[Any]]] = None,
        add_slash: bool = True,
    ) -> None:
        super().__init__()
        self.client = client
        self._base_url = base_url
        self._request_params = request_params
        self.count_mapper = count_mapper or LambdaMapper(
            lambda x: len(cast(List[Any], x))
        )

        self.list_mapper = list_mapper or LambdaMapper(lambda x: cast(List[Any], x))
        self.add_slash = add_slash

    @property
    def base_url(self):
        """Return the base URL of the resource.

        You can override this to customize the behavior.
        """
        if self._base_url is not None:  # pragma: nocover
            return self._base_url
        return ""

    @property
    def request_params(self):
        """Return additional request parameters.

        This is the easyest way to customize the request headers and query parameters.
        """
        params = {}

        if self._request_params is not None:  # pragma nocover
            params.update(self._request_params)

        return params

    async def process_response(self, response: httpx.Response) -> Any:
        """Processes the response coming from the HTTP server.

        Args:
            response: The response result.

        Returns:
            Any: The response raw data.
        """
        self._ensure_success(response)

        if response.status_code == HTTPStatus.NO_CONTENT:
            return None
        elif (
            response.status_code >= 300 and response.status_code < 400
        ):  # pragma nocover
            raise RuntimeError("A redirect found.")

        try:
            if self.is_json(response):
                return response.json()
            else:  # pragma nocover
                # Return the response text representation:
                return response.text
        finally:
            await response.aclose()

    @classmethod
    def _ensure_success(cls, response):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as ex:
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise ItemNotFoundException("Cannot find the remote resource.") from ex
            elif response.status_code in (
                HTTPStatus.BAD_REQUEST,
                HTTPStatus.UNPROCESSABLE_ENTITY,
            ):
                raise InvalidPayloadException() from ex
            else:
                raise

    @classmethod
    def is_json(cls, response: httpx.Response) -> bool:
        """Checks if the response contains JSON data.

        Args:
            response: The response to be checked.

        Returns:
            bool: `True` if the response is a JSON document, false otherwise.
        """
        content_type, _ = cgi.parse_header(response.headers.get("content-type"))
        _main_type, sub_type = content_type.split("/")
        is_json = sub_type.startswith("json")
        return is_json

    async def get_by_id(self, item_id: str, **kwargs: Any) -> Any:
        """Return a resource by it's ID.

        Args:
            item_id: The ID of the resource to retrieve.

        Returns:
            Any: The resource as Json.
        """
        return await self.process_response(
            await self.client.get(
                self.get_id_url(item_id), **self._merge_params(kwargs)
            )
        )

    async def _get_list(self, *, offset=None, size=None, **query_filters):
        params = {}
        if size is not None:
            params.update(size=size)
        if offset is not None:
            params.update(offset=offset)

        request_params = self._merge_params(query_filters, params)
        return await self.process_response(
            await self.client.get(self.list_url, **request_params)
        )

    def _merge_params(
        self, query_filters: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ):
        if params is None:
            params = {}
        request_params = {
            "params": {
                **self.request_params.get("params", {}),
                **query_filters.get("params", {}),
                **params,
            },
            "headers": {
                **self.request_params.get("headers", {}),
                **query_filters.get("headers", {}),
            },
            "cookies": {
                **self.request_params.get("cookies", {}),
                **query_filters.get("cookies", {}),
            },
        }

        return request_params

    @property
    def list_url(self):
        """Retrieve the real base_url.

        Returns:
            str: The base URL built from the passed base url in the constructor.

        >>> base_url = 'https://example.com/resource'
        >>> repo = HttpRepository(
        ...     httpx.AsyncClient(),
        ...     base_url=base_url,
        ...     add_slash=False,
        ... )
        >>> repo.list_url
        'https://example.com/resource'
        >>> repo2 = HttpRepository(
        ...     repo.client, base_url=base_url, add_slash=True
        ... )
        >>> repo2.list_url
        'https://example.com/resource/'
        >>>
        """
        list_url = self.base_url
        if self.add_slash:
            list_url = f"{list_url}/"
        return list_url

    async def get_list(self, **query_filters):
        """Return a list of items.

        Args:
            offset (int, optional): Where to start from.. Defaults to None.
            size (int, optional): How many items to retrieve. Defaults to None.

        Returns:
            list: Items from the remote source.

        """
        return self.list_mapper(await self._get_list(**query_filters))

    async def get_count(self, **query_filters: Any) -> int:
        """Return how many items the remote source have in it's database.

        Returns:
            int: How many items.
        """
        return self.count_mapper(await self._get_list(**query_filters))

    async def add(self, payload: Any, **kwargs: Any) -> Any:
        """Add a new item to the remote resource.

        Args:
            payload: A payload to use as the data source.

        Returns:
            Any: The newly created item.
        """
        extra_data = kwargs.pop("extra_data", None)
        if extra_data is not None:
            if not isinstance(payload, dict):
                raise ValueError("Cannot update the payload with the extra data.")
            elif not isinstance(extra_data, dict):
                raise ValueError("Invalid extra data provided.")
            else:
                # The real data takes presedence:
                payload = {**extra_data, **payload}

        return await self.process_response(
            await self.client.post(
                self.list_url, json=payload, **self._merge_params(kwargs, extra_data)
            )
        )

    async def update(self, item_id: str, payload: Any, **kwargs: Any) -> Any:
        """Update the remote resource.

        Args:
            item_id: The resource ID.
            payload: The payload to send. Must be json-compatible.

        Returns:
            Any: Json-compatibel updated data.
        """
        return await self.process_response(
            await self.client.patch(
                self.get_id_url(item_id), json=payload, **self._merge_params(kwargs)
            )
        )

    def get_id_url(self, item_id):
        """Returns the URL for an item id.

        Args:
            item_id: The item ID to get URL for.

        Returns:
            str: The URL of the item ID.
        """
        return f"{self.base_url}/{item_id}"

    async def replace(self, item_id: str, payload: Any, **kwargs: Any):
        """Send a replace request.

        Args:
            item_id: The resource ID to replace.
            payload (Any): The new data for the resource.

        Returns:
            Any: The newly updated resource.
        """
        return await self.process_response(
            await self.client.put(self.get_id_url(item_id), json=payload)
        )

    async def remove(self, item_id: str, **kwargs: Any):
        """Remove the specified remote resource.

        Args:
            item_id: The resource ID to remove.
        """
        await self.process_response(
            await self.client.delete(
                self.get_id_url(item_id), **self._merge_params(kwargs)
            )
        )
