# Copyright 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from typing import Iterable, Any, Optional, Dict, List, Tuple, Type, TYPE_CHECKING

import jmespath
from botocore import xform_name
from botocore.model import ServiceModel

from boto3.resources.params import get_data_member
from boto3.resources.model import Parameter, ResponseResource
from boto3.resources.base import ServiceResource
from boto3.utils import ServiceContext

if TYPE_CHECKING:
    from boto3.resources.factory import ResourceFactory
else:
    ResourceFactory = object


def all_not_none(iterable: Iterable[Any]) -> bool:
    """
    Return True if all elements of the iterable are not None (or if the
    iterable is empty). This is like the built-in ``all``, except checks
    against None, so 0 and False are allowable values.
    """
    for element in iterable:
        if element is None:
            return False
    return True


def build_identifiers(
    identifiers: Iterable[Parameter],
    parent: ServiceResource,
    params: Optional[Dict[str, Any]] = None,
    raw_response: Optional[Dict[str, Any]] = None,
) -> List[Tuple[str, Any]]:
    """
    Builds a mapping of identifier names to values based on the
    identifier source location, type, and target. Identifier
    values may be scalars or lists depending on the source type
    and location.

    :type identifiers: list
    :param identifiers: List of :py:class:`~boto3.resources.model.Parameter`
                        definitions
    :type parent: ServiceResource
    :param parent: The resource instance to which this action is attached.
    :type params: dict
    :param params: Request parameters sent to the service.
    :type raw_response: dict
    :param raw_response: Low-level operation response.
    :rtype: list
    :return: An ordered list of ``(name, value)`` identifier tuples.
    """
    results = []

    for identifier in identifiers:
        source = identifier.source
        target = identifier.target

        if source == 'response':
            value = jmespath.search(identifier.path, raw_response)
        elif source == 'requestParameter':
            value = jmespath.search(identifier.path, params)
        elif source == 'identifier':
            value = getattr(parent, xform_name(identifier.name))
        elif source == 'data':
            # If this is a data member then it may incur a load
            # action before returning the value.
            value = get_data_member(parent, identifier.path)
        elif source == 'input':
            # This value is set by the user, so ignore it here
            continue
        else:
            raise NotImplementedError(
                'Unsupported source type: {0}'.format(source))

        results.append((xform_name(target), value))

    return results


def build_empty_response(search_path: str, operation_name: str, service_model: ServiceModel) -> Any:
    """
    Creates an appropriate empty response for the type that is expected,
    based on the service model's shape type. For example, a value that
    is normally a list would then return an empty list. A structure would
    return an empty dict, and a number would return None.

    :type search_path: string
    :param search_path: JMESPath expression to search in the response
    :type operation_name: string
    :param operation_name: Name of the underlying service operation.
    :type service_model: :ref:`botocore.model.ServiceModel`
    :param service_model: The Botocore service model
    :rtype: dict, list, or None
    :return: An appropriate empty value
    """
    response = None

    operation_model = service_model.operation_model(operation_name)
    shape = operation_model.output_shape

    if search_path:
        # Walk the search path and find the final shape. For example, given
        # a path of ``foo.bar[0].baz``, we first find the shape for ``foo``,
        # then the shape for ``bar`` (ignoring the indexing), and finally
        # the shape for ``baz``.
        for item in search_path.split('.'):
            item = item.strip('[0123456789]$')

            if shape.type_name == 'structure':
                shape = shape.members[item]
            elif shape.type_name == 'list':
                shape = shape.member
            else:
                raise NotImplementedError(
                    'Search path hits shape type {0} from {1}'.format(
                        shape.type_name, item))

    # Anything not handled here is set to None
    if shape.type_name == 'structure':
        return {}
    elif shape.type_name == 'list':
        return []
    elif shape.type_name == 'map':
        return {}

    return None


class RawHandler(object):
    """
    A raw action response handler. This passed through the response
    dictionary, optionally after performing a JMESPath search if one
    has been defined for the action.

    :type search_path: string
    :param search_path: JMESPath expression to search in the response
    :rtype: dict
    :return: Service response
    """
    def __init__(self, search_path: str) -> None:
        self.search_path = search_path

    def __call__(self, parent: ServiceResource, params: Dict[str, Any], response: Dict[str, Any]) -> Any:
        """
        :type parent: ServiceResource
        :param parent: The resource instance to which this action is attached.
        :type params: dict
        :param params: Request parameters sent to the service.
        :type response: dict
        :param response: Low-level operation response.
        """
        # TODO: Remove the '$' check after JMESPath supports it
        if self.search_path and self.search_path != '$':
            response = jmespath.search(self.search_path, response)

        return response


class ResourceHandler(object):
    """
    Creates a new resource or list of new resources from the low-level
    response based on the given response resource definition.

    :type search_path: string
    :param search_path: JMESPath expression to search in the response

    :type factory: ResourceFactory
    :param factory: The factory that created the resource class to which
                    this action is attached.

    :type resource_model: :py:class:`~boto3.resources.model.ResponseResource`
    :param resource_model: Response resource model.

    :type service_context: :py:class:`~boto3.utils.ServiceContext`
    :param service_context: Context about the AWS service

    :type operation_name: string
    :param operation_name: Name of the underlying service operation, if it
                           exists.

    :rtype: ServiceResource or list
    :return: New resource instance(s).
    """
    def __init__(
        self,
        search_path: str,
        factory: ResourceFactory,
        resource_model: ResponseResource,
        service_context: ServiceContext,
        operation_name: Optional[str] = None,
    ):
        self.search_path = search_path
        self.factory = factory
        self.resource_model = resource_model
        self.operation_name = operation_name
        self.service_context = service_context

    def __call__(self, parent: ServiceResource, params: Dict[str, Any], response: Dict[str, Any]) -> Any:
        """
        :type parent: ServiceResource
        :param parent: The resource instance to which this action is attached.
        :type params: dict
        :param params: Request parameters sent to the service.
        :type response: dict
        :param response: Low-level operation response.
        """
        resource_name = self.resource_model.type
        json_definition = self.service_context.resource_json_definitions.get(
            resource_name)

        # Load the new resource class that will result from this action.
        resource_cls = self.factory.load_from_definition(
            resource_name=resource_name,
            single_resource_json_definition=json_definition,
            service_context=self.service_context
        )
        raw_response = response
        search_response = None

        # Anytime a path is defined, it means the response contains the
        # resource's attributes, so resource_data gets set here. It
        # eventually ends up in resource.meta.data, which is where
        # the attribute properties look for data.
        if self.search_path:
            search_response = jmespath.search(self.search_path, raw_response)

        # First, we parse all the identifiers, then create the individual
        # response resources using them. Any identifiers that are lists
        # will have one item consumed from the front of the list for each
        # resource that is instantiated. Items which are not a list will
        # be set as the same value on each new resource instance.
        identifiers = dict(build_identifiers(
            self.resource_model.identifiers, parent, params,
            raw_response))

        # If any of the identifiers is a list, then the response is plural
        plural = [v for v in identifiers.values() if isinstance(v, list)]
        result: Any

        if plural:
            result = []

            # The number of items in an identifier that is a list will
            # determine how many resource instances to create.
            for i in range(len(plural[0])):
                # Response item data is *only* available if a search path
                # was given. This prevents accidentally loading unrelated
                # data that may be in the response.
                response_item = None
                if search_response:
                    response_item = search_response[i]
                result.append(
                    self.handle_response_item(resource_cls, parent,
                                              identifiers, response_item))
        elif all_not_none(identifiers.values()):
            # All identifiers must always exist, otherwise the resource
            # cannot be instantiated.
            result = self.handle_response_item(
                resource_cls, parent, identifiers, search_response)
        else:
            # The response should be empty, but that may mean an
            # empty dict, list, or None based on whether we make
            # a remote service call and what shape it is expected
            # to return.
            result = None
            if self.operation_name is not None:
                # A remote service call was made, so try and determine
                # its shape.
                result = build_empty_response(
                    self.search_path, self.operation_name,
                    self.service_context.service_model)

        return result

    def handle_response_item(
        self,
        resource_cls: Type[ServiceResource],
        parent: ServiceResource,
        identifiers: Dict[str, Any],
        resource_data: Optional[Dict[str, Any]],
    ):
        """
        Handles the creation of a single response item by setting
        parameters and creating the appropriate resource instance.

        :type resource_cls: ServiceResource subclass
        :param resource_cls: The resource class to instantiate.
        :type parent: ServiceResource
        :param parent: The resource instance to which this action is attached.
        :type identifiers: dict
        :param identifiers: Map of identifier names to value or values.
        :type resource_data: dict or None
        :param resource_data: Data for resource attributes.
        :rtype: ServiceResource
        :return: New resource instance.
        """
        kwargs = {
            'client': parent.meta.client,
        }

        for name, value in identifiers.items():
            # If value is a list, then consume the next item
            if isinstance(value, list):
                value = value.pop(0)

            kwargs[name] = value

        resource = resource_cls(**kwargs)

        if resource_data is not None:
            resource.meta.data = resource_data

        return resource
