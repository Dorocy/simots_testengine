from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from aas_test_engines.test_cases.v3_0.parse_submodel import LangString
from aas_test_engines.test_cases.v3_0.submodel_templates import template

@dataclass
class UnnamedElement0:
    image_file: str = field(metadata={
    'semantic_id': '0173-1#02-ABK291#002'
})
    image_note: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-ABL423#001'
})

@dataclass
class ProductImages:
    unnamed_element_0: Optional[UnnamedElement0] = field(metadata={
    'semantic_id': '0173-1#02-ABM220#001/0173-1#01-AHY911#001'
})

@dataclass
class GeneralInformation:
    manufacturer_name: str = field(metadata={
    'semantic_id': '0173-1#02-AAO677#004'
})
    company_logo: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABI776#002'
})
    manufacturer_product_designation: LangString = field(metadata={
    'semantic_id': '0173-1#02-AAW338#003'
})
    manufacturer_article_number: str = field(metadata={
    'semantic_id': '0173-1#02-AAO676#005'
})
    manufacturer_order_code: str = field(metadata={
    'semantic_id': '0173-1#02-AAO227#004'
})
    product_images: Optional[List[ProductImages]] = field(metadata={
    'semantic_id': '0173-1#02-ABM220#001'
})

@dataclass
class UnnamedElement1:
    classification_system: str = field(metadata={
    'semantic_id': '0173-1#02-ABL424#001'
})
    classification_system_version: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAR710#003'
})
    classification_system_url: Optional[str] = field(metadata={
    'semantic_id': 'https://admin-shell.io/IDTA/TechnicalData/ProductClassifications/ProduktClassification/ClassificationSystemUrl/2/0'
})
    product_class_id: str = field(metadata={
    'semantic_id': '0173-1#02-ABG776#003'
})
    product_class_coded_name: str = field(metadata={
    'semantic_id': '0173-1#02-ABK128#002'
})
    product_class_name: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-ABK273#002'
})

@dataclass
class ProductClassifications:
    unnamed_element_1: Optional[UnnamedElement1] = field(metadata={
    'semantic_id': '0173-1#02-ABK162#002/0173-1#01-AHX839#002'
})

@dataclass
class UnnamedElement2:
    pass

@dataclass
class TechnicalPropertyAreas:
    unnamed_element_2: Optional[UnnamedElement2] = field(metadata={
    'semantic_id': '0173-1#02-ABL358#002/0173-1#01-AHX773#002'
})

@dataclass
class FurtherInformation:
    text_statement: Optional[List[LangString]] = field(metadata={
    'semantic_id': '0173-1#02-ABK134#002'
})
    valid_date: str = field(metadata={
    'semantic_id': '0173-1#02-ABL775#001'
})

@dataclass
class UnnamedElement3:
    pass

@dataclass
class SpecificDescriptions:
    unnamed_element_3: Optional[UnnamedElement3] = field(metadata={
    'semantic_id': '0173-1#02-ABM221#001/0173-1#01-AHY912#001'
})

@dataclass
@template("0173-1#01-AHX837#002")
class TechnicalData:
    general_information: GeneralInformation = field(metadata={
    'semantic_id': '0173-1#02-ABK161#002/0173-1#01-AHX838#002'
})
    product_classifications: Optional[List[ProductClassifications]] = field(metadata={
    'semantic_id': '0173-1#02-ABK162#002'
})
    technical_property_areas: Optional[List[TechnicalPropertyAreas]] = field(metadata={
    'semantic_id': '0173-1#02-ABK163#002'
})
    further_information: Optional[FurtherInformation] = field(metadata={
    'semantic_id': '0173-1#02-ABK164#002'
})
    specific_descriptions: Optional[List[SpecificDescriptions]] = field(metadata={
    'semantic_id': '0173-1#02-ABM221#001'
})


