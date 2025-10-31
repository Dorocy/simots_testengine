from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from aas_test_engines.test_cases.v3_0.parse_submodel import LangString
from aas_test_engines.test_cases.v3_0.submodel_templates import template

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


