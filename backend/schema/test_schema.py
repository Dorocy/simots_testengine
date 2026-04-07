from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from aas_test_engines.test_cases.v3_0.parse_submodel import LangString
from aas_test_engines.test_cases.v3_0.submodel_templates import template

class RoleOfContactPerson(Enum):
    administrativ_contact = "0173-1#07-AAS927#001"
    commercial_contact = "0173-1#07-AAS928#001"
    other_contact = "0173-1#07-AAS929#001"
    hazardous_goods_contact = "0173-1#07-AAS930#001"
    technical_contact = "0173-1#07-AAS931#001"

class TypeOfTelephone(Enum):
    office = "0173-1#07-AAS754#001"
    office_mobile = "0173-1#07-AAS755#001"
    secretary = "0173-1#07-AAS756#001"
    substitute = "0173-1#07-AAS757#001"
    home = "0173-1#07-AAS758#001"
    private_mobile = "0173-1#07-AAS759#001"

class TypeOfFaxNumber(Enum):
    office = "0173-1#07-AAS754#001"
    secretary = "0173-1#07-AAS756#001"
    home = "0173-1#07-AAS758#001"

class TypeOfEmailAddress(Enum):
    office = "0173-1#07-AAS754#001"
    secretary = "0173-1#07-AAS756#001"
    substitute = "0173-1#07-AAS757#001"
    home = "0173-1#07-AAS758#001"

@dataclass
class Phone:
    telephone_number: LangString = field(metadata={
    'semantic_id': '0173-1#02-AAO136#002'
})
    type_of_telephone: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAO137#003'
})
    available_time: Optional[LangString] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/'
})

@dataclass
class Fax:
    fax_number: LangString = field(metadata={
    'semantic_id': '0173-1#02-AAO195#002'
})
    type_of_fax_number: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAO196#003'
})

@dataclass
class Email:
    email_address: str = field(metadata={
    'semantic_id': '0173-1#02-AAO198#002'
})
    public_key: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO200#002'
})
    type_of_email_address: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAO199#003'
})
    type_of_public_key: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO201#002'
})

@dataclass
class Ipcommunication00:
    address_of_additional_link: str = field(metadata={
    'semantic_id': '0173-1#02-AAQ326#002'
})
    type_of_communication: Optional[str] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ ContactInformations/ContactInformation/IPCommunication/TypeOfCommunication'
})
    available_time: Optional[LangString] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/'
})

@dataclass
class ContactInformation:
    role_of_contact_person: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAO204#003'
})
    national_code: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO134#002'
})
    language: Optional[List[str]] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Language'
})
    time_zone: Optional[str] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/TimeZone'
})
    city_town: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO132#002'
})
    company: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAW001#001'
})
    department: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO127#003'
})
    phone: Optional[Phone] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Phone'
})
    fax: Optional[Fax] = field(metadata={
    'semantic_id': '0173-1#02-AAQ834#005'
})
    email: Optional[Email] = field(metadata={
    'semantic_id': '0173-1#02-AAQ836#005'
})
    ipcommunication__00__: Optional[List[Ipcommunication00]] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/'
})
    street: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO128#002'
})
    zipcode: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO129#002'
})
    pobox: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO130#002'
})
    zip_code_of_pobox: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO131#002'
})
    state_county: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO133#002'
})
    name_of_contact: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO205#002'
})
    first_name: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO206#002'
})
    middle_names: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO207#002'
})
    title: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO208#003'
})
    academic_title: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO209#003'
})
    further_details_of_contact: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-AAO210#002'
})
    address_of_additional_link: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAQ326#002'
})

@dataclass
@template("https://admin-shell.io/zvei/nameplate/1/0/ContactInformations")
class ContactInformations:
    contact_information: List[ContactInformation] = field(metadata={
    'semantic_id': 'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation'
})


