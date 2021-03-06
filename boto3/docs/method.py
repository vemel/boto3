# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from typing import TYPE_CHECKING, Any, List, Optional

from botocore.docs.bcdoc.restdoc import DocumentStructure
from botocore.docs.method import document_model_driven_method
from botocore.docs.utils import DocumentedShape
from botocore.hooks import BaseEventHooks
from botocore.model import OperationModel

# pylint: disable=cyclic-import
if TYPE_CHECKING:
    from boto3.resources.action import Action
    from boto3.resources.model import ResponseResource
else:
    Action = object()
    ResponseResource = object()


def document_model_driven_resource_method(
    section: DocumentStructure,
    method_name: str,
    operation_model: OperationModel,
    event_emitter: BaseEventHooks,
    resource_action_model: Action,
    method_description: Optional[str] = None,
    example_prefix: Optional[str] = None,
    include_input: Optional[List[DocumentedShape]] = None,
    include_output: Optional[List[DocumentedShape]] = None,
    exclude_input: Optional[List[Any]] = None,
    exclude_output: Optional[List[Any]] = None,
    document_output: bool = True,
    include_signature: bool = True,
) -> None:

    document_model_driven_method(
        section=section,
        method_name=method_name,
        operation_model=operation_model,
        event_emitter=event_emitter,
        method_description=method_description,
        example_prefix=example_prefix,
        include_input=include_input,
        include_output=include_output,
        exclude_input=exclude_input,
        exclude_output=exclude_output,
        document_output=document_output,
        include_signature=include_signature,
    )

    # If this action returns a resource modify the return example to
    # appropriately reflect that.
    if resource_action_model.has_resource():
        if "return" in section.available_sections:
            section.delete_section("return")
        resource_type = resource_action_model.resource.type

        new_return_section = section.add_new_section("return")
        return_resource_type = "%s.%s" % (
            operation_model.service_model.service_name,
            resource_type,
        )

        return_type = ":py:class:`%s`" % return_resource_type
        return_description = "%s resource" % (resource_type)

        if _method_returns_resource_list(resource_action_model.resource):
            return_type = "list(%s)" % return_type
            return_description = "A list of %s resources" % (resource_type)

        new_return_section.style.new_line()
        new_return_section.write(":rtype: %s" % return_type)
        new_return_section.style.new_line()
        new_return_section.write(":returns: %s" % return_description)
        new_return_section.style.new_line()


def _method_returns_resource_list(resource: ResponseResource) -> bool:
    for identifier in resource.identifiers:
        if identifier.path and "[]" in identifier.path:
            return True

    return False
