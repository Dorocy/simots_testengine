
#모든 소스코드 파일에서 해당 부분은 default import되어야함.
from aas_test_engines.test_cases.v3_0.parse_submodel import LangString
from aas_test_engines.test_cases.v3_0.submodel_templates import template
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from aas_test_engines.test_cases_v3.0.c


class EntType(Enum):
	co_managed_entity = "CoManagedEntity"
	self_managed_entity = "SelfManagedEntity"

@dataclass
class DocumentId00:
    document_domain_id: str = field(metadata={
    'semantic_id': '0173-1#02-ABH994#003'})

    document_identifier: str = field(metadata={
    'semantic_id': '0173-1#02-AAO099#004'})
    document_is_primary: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABH995#004'})
@dataclass
class DocumentClassification00:
    class_id: str = field(metadata={
    'semantic_id': '0173-1#02-ABH996#003'})
    class_name: LangString = field(metadata={
    'semantic_id': '0173-1#02-ABJ219#003'})
    classification_system: str = field(metadata={
    'semantic_id': '0173-1#02-ABH997#003'})

@dataclass
class DocumentVersion00:
    language__00__: List[str] = field(metadata={
    'semantic_id': '0173-1#02-AAN468#009'})
    version: str = field(metadata={
    'semantic_id': '0173-1#02-AAP003#005'})
    title: LangString = field(metadata={
    'semantic_id': '0173-1#02-ABG940#004'})
    sub_title: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-ABH998#003'})
    description: LangString = field(metadata={
    'semantic_id': '0173-1#02-AAN466#004'})
    key_words: LangString = field(metadata={
    'semantic_id': '0173-1#02-ABH999#003'})
    status_set_date: str = field(metadata={
    'semantic_id': '0173-1#02-ABI000#003'})
    status_value: str = field(metadata={
    'semantic_id': '0173-1#02-ABI001#003'})
    organization_short_name: str = field(metadata={
    'semantic_id': '0173-1#02-ABI002#003'})
    organization_official_name: str = field(metadata={
    'semantic_id': '0173-1#02-ABI004#003'})
    refers_to__00__: Optional[List[RefType]] = field(metadata={
    'semantic_id': '0173-1#02-ABK288#002'})
    based_on__00__: Optional[List[RefType]] = field(metadata={
    'semantic_id': '0173-1#02-ABK289#002'})
    translation_of__00__: Optional[List[RefType]] = field(metadata={
    'semantic_id': '0173-1#02-ABK290#002'})
    digital_file__00__: List[str] = field(metadata={
    'semantic_id': '0173-1#02-ABK126#003'})
    preview_file__00__: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABK127#002'})
@dataclass
class Document00:
    document_id__00__: List[DocumentId00] = field(metadata={
    'semantic_id': '0173-1#02-ABI501#003/0173-1#01-AHF580#001*03'})
    document_classification__00__: List[DocumentClassification00] = field(metadata={
    'semantic_id': '0173-1#02-ABI502#003/0173-1#01-AHF581#003*01'})
    document_version__00__: Optional[List[DocumentVersion00]] = field(metadata={
    'semantic_id': '0173-1#02-ABI503#003/0173-1#01-AHF582#003*01'})
    documented_entity__00__: Optional[List[RefType]] = field(metadata={
    'semantic_id': 'https://admin-shell.io/vdi/2770/1/0/Document/DocumentedEntity'})
    
@dataclass
@template("0173-1#0-AHF578#003")
class HandoverDocumentation:
    number_of_documents: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABH990#001'})
    document__00__: Optional[List[Document00]] = field(metadata={
    'semantic_id': '0173-1#02-ABI500#003/0173-1#01-AHF579#003*01'})
    entity: Optional[List[EntType]] = field(metadata={
    'semantic_id': 'https://admin-shell.io/vdi/2770/1/0/EntityForDocumentation'})