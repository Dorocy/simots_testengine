from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from aas_test_engines.test_cases.v3_0.parse_submodel import LangString
from aas_test_engines.test_cases.v3_0.submodel_templates import template

@dataclass
class UnnamedElement1:
    image_note: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-ABL423#001'
})

@dataclass
class ProductImages:
    unnamed_element_1: Optional[UnnamedElement1] = field(metadata={
    'semantic_id': '0173-1#02-ABM220#001/0173-1#01-AHY911#001'
})

@dataclass
class GeneralInformation:
    manufacturer_name: str = field(metadata={
    'semantic_id': '0173-1#02-AAO677#004'
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
class UnnamedElement2:
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
    unnamed_element_2: Optional[UnnamedElement2] = field(metadata={
    'semantic_id': '0173-1#02-ABK162#002/0173-1#01-AHX839#002'
})

@dataclass
class UnnamedElement3:
    pass

@dataclass
class TechnicalPropertyAreas:
    unnamed_element_3: Optional[UnnamedElement3] = field(metadata={
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
class UnnamedElement4:
    pass

@dataclass
class SpecificDescriptions:
    unnamed_element_4: Optional[UnnamedElement4] = field(metadata={
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


@dataclass
class UnnamedElement0:
    marking_name: str = field(metadata={
    'semantic_id': '0112/2///61987#ABA231#009'
})
    designation_of_certificate_or_approval: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABH783#003'
})
    issue_date: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABO097#001'
})
    expiry_date: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABH830#002'
})
    marking_additional_text: Optional[List[str]] = field(metadata={
    'semantic_id': '0112/2///61987#ABB146#007'
})

@dataclass
class Markings:
    unnamed_element_0: List[UnnamedElement0] = field(metadata={
    'semantic_id': '0112/2///61360_7#AAS009#001'
})

@dataclass
class AssetSpecificProperties:
    pass

@dataclass
@template("https://admin-shell.io/idta/nameplate/3/0/Nameplate")
class Nameplate:
    uriof_the_product: str = field(metadata={
    'semantic_id': '0112/2///61987#ABN590#002'
})
    manufacturer_name: LangString = field(metadata={
    'semantic_id': '0112/2///61987#ABA565#009'
})
    manufacturer_product_designation: LangString = field(metadata={
    'semantic_id': '0112/2///61987#ABA567#009'
})
    manufacturer_product_root: Optional[LangString] = field(metadata={
    'semantic_id': '0112/2///61360_7#AAS011#001'
})
    manufacturer_product_family: Optional[LangString] = field(metadata={
    'semantic_id': '0112/2///61987#ABP464#002'
})
    manufacturer_product_type: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABA300#008'
})
    order_code_of_manufacturer: str = field(metadata={
    'semantic_id': '0112/2///61987#ABA950#008'
})
    product_article_number_of_manufacturer: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABA581#007'
})
    serial_number: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABA951#009'
})
    year_of_construction: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABP000#002'
})
    date_of_manufacture: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABB757#007'
})
    hardware_version: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABA926#008'
})
    firmware_version: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABA302#006'
})
    software_version: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABA601#008'
})
    country_of_origin: Optional[str] = field(metadata={
    'semantic_id': '0112/2///61987#ABP462#001'
})
    unique_facility_identifier: Optional[str] = field(metadata={
    'semantic_id': 'https://admin-shell.io/idta/nameplate/3/0/UniqueFacilityIdentifier'
})
    markings: Optional[Markings] = field(metadata={
    'semantic_id': '0112/2///61360_7#AAS006#001'
})
    asset_specific_properties: Optional[AssetSpecificProperties] = field(metadata={
    'semantic_id': '0173-1#02-ABI218#003/0173-1#01-AGZ672#004'
})


