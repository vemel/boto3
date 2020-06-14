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
import inspect
from typing import Any

from botocore.compat import OrderedDict
from botocore.client import BaseClient
from botocore.docs.bcdoc.restdoc import DocumentStructure

from boto3.resources.base import ServiceResource
from boto3.resources.model import ResourceModel

class BotocoreSignatureMixin:
    @classmethod
    def _add_custom_method(cls, section: DocumentStructure, name: str, method: Any) -> None:
        cls._document_custom_signature(
            section, name, method)
        method_intro_section = section.add_new_section('method-intro')
        method_intro_section.writeln('')
        doc_string = inspect.getdoc(method)
        if doc_string is not None:
            method_intro_section.style.write_py_doc_string(doc_string)

    @staticmethod
    def _document_custom_signature(section: DocumentStructure, name: str, method: Any) -> None:
        signature = inspect.signature(method)
        signature_params = ", ".join(signature.parameters)
        section.style.start_sphinx_py_method(name, signature_params)


class BaseDocumenter(BotocoreSignatureMixin):
    def __init__(self, resource: ServiceResource) -> None:
        self._resource = resource
        assert self._resource.meta.client
        self._client = self._resource.meta.client
        assert self._resource.meta.resource_model
        self._resource_model = self._resource.meta.resource_model
        self._service_model = self._client.meta.service_model
        self._resource_name = self._resource_model.name
        self._service_name = self._service_model.service_name
        self._service_docs_name = self._client.__class__.__name__
        self.member_map = OrderedDict()
        self.represents_service_resource = (
            self._service_name == self._resource_name)

    @property
    def class_name(self) -> str:
        return '%s.%s' % (self._service_docs_name, self._resource_name)

    @property
    def resource_model(self) -> ResourceModel:
        return self._resource_model

    @property
    def client(self) -> BaseClient:
        return self._client
