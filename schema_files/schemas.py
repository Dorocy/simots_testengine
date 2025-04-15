from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from aas_test_engines.test_cases.v3_0.parse_submodel import LangString
from aas_test_engines.test_cases.v3_0.submodel_templates import template


class EntityType(Enum):
	co_managed_entity = "CoManagedEntity"
	self_managed_entity = "SelfManagedEntity"

class EntityValue:
    entity_type: EntityType

    class_name: LangString = field(metadata={"semantic_id": "0173-1#02-ABJ219#003"})
    
    class_name: LangString = field(metadata={'semantic_id': '0173-1#02-ABJ219#004'})

@dataclass
class DocumentId00:
    document_domain_id: str = field(metadata={
    'semantic_id': '0173-1#02-ABH994#003'
})
    document_identifier: str = field(metadata={
    'semantic_id': '0173-1#02-AAO099#004'
})
    document_is_primary: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABH995#004'
})

@dataclass
class DocumentClassification00:
    class_id: str = field(metadata={
    'semantic_id': '0173-1#02-ABH996#003'
})
    class_name: LangString = field(metadata={
    'semantic_id': '0173-1#02-ABJ219#003'
})
    classification_system: str = field(metadata={
    'semantic_id': '0173-1#02-ABH997#003'
})

@dataclass
class DocumentVersion00:
    language__00__: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-AAN468#009'
})
    version: str = field(metadata={
    'semantic_id': '0173-1#02-AAP003#005'
})
    title: LangString = field(metadata={
    'semantic_id': '0173-1#02-ABG940#004'
})
    sub_title: Optional[LangString] = field(metadata={
    'semantic_id': '0173-1#02-ABH998#003'
})
    description: LangString = field(metadata={
    'semantic_id': '0173-1#02-AAN466#004'
})
    key_words: LangString = field(metadata={
    'semantic_id': '0173-1#02-ABH999#003'
})
    status_set_date: str = field(metadata={
    'semantic_id': '0173-1#02-ABI000#003'
})
    status_value: str = field(metadata={
    'semantic_id': '0173-1#02-ABI001#003'
})
    organization_short_name: str = field(metadata={
    'semantic_id': '0173-1#02-ABI002#003'
})
    organization_official_name: str = field(metadata={
    'semantic_id': '0173-1#02-ABI004#003'
})
    refers_to__00__: Optional[List[str]] = field(metadata={
    'semantic_id': '0173-1#02-ABK288#002'
})
    based_on__00__: Optional[List[str]] = field(metadata={
    'semantic_id': '0173-1#02-ABK289#002'
})
    translation_of__00__: Optional[List[str]] = field(metadata={
    'semantic_id': '0173-1#02-ABK290#002'
})
    digital_file__00__: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABK126#003'
})
    preview_file__00__: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABK127#002'
})

@dataclass
class Document00:
    document_id__00__: Optional[DocumentId00] = field(metadata={
    'semantic_id': '0173-1#02-ABI501#003/0173-1#01-AHF580#001*03'
})
    document_classification__00__: Optional[DocumentClassification00] = field(metadata={
    'semantic_id': '0173-1#02-ABI502#003/0173-1#01-AHF581#003*01'
})
    document_version__00__: Optional[List[DocumentVersion00]] = field(metadata={
    'semantic_id': '0173-1#02-ABI503#003/0173-1#01-AHF582#003*01'
})
    documented_entity__00__: Optional[List[str]] = field(metadata={
    'semantic_id': 'https://admin-shell.io/vdi/2770/1/0/Document/DocumentedEntity'
})

@dataclass
@template("0173-1#01-AHF578#003")
class HandoverDocumentation:
    number_of_documents: Optional[str] = field(metadata={
    'semantic_id': '0173-1#02-ABH990#001'
})
    document__00__: Optional[List[Document00]] = field(metadata={
    'semantic_id': '0173-1#02-ABI500#003/0173-1#01-AHF579#003*01'
})
    entity: Optional[List[EntityType]] = field(metadata={
    'semantic_id': 'https://admin-shell.io/vdi/2770/1/0/EntityForDocumentation'
})


class RoleOfContactPerson(Enum):
    Administrative = "0173-1#07-AAS927#001"
    Commercial = "0173-1#07-AAS928#001"
    Other = "0173-1#07-AAS929#001"
    HazardousGoods = "0173-1#07-AAS930#001"
    Technical = "0173-1#07-AAS931#001"


class TypeOfTelephone(Enum):
    Office = "0173-1#07-AAS754#001"
    OfficeMobile = "0173-1#07-AAS755#001"
    Secretary = "0173-1#07-AAS756#001"
    Substitute = "0173-1#07-AAS757#001"
    Home = "0173-1#07-AAS758#001"
    PrivateMobile = "0173-1#07-AAS759#001"


@dataclass
class Phone:
    telephone_number: LangString = field(
        metadata={
            "semantic_id": "0173-1#02-AAO136#002",
        }
    )
    type_of_telephone: Optional[TypeOfTelephone] = field(metadata={"semantic_id": "0173-1#02-AAO137#003"})
    available_time: Optional[LangString] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/",
        }
    )


class TypeOfFaxNumber(Enum):
    Office = "0173-1#07-AAS754#001"
    Secretary = "0173-1#07-AAS756#001"
    Home = "0173-1#07-AAS758#001"


@dataclass
class Fax:
    fax_number: LangString = field(
        metadata={
            "semantic_id": "0173-1#02-AAO195#002",
        }
    )
    type_of_fax_number: Optional[TypeOfFaxNumber] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO196#003",
        }
    )


class TypeOfEmailAddress(Enum):
    Office = "0173-1#07-AAS754#001"
    Secretary = "0173-1#07-AAS756#001"
    Substitute = "0173-1#07-AAS757#001"
    Home = "0173-1#07-AAS758#001"


@dataclass
class Email:
    email_address: str = field(
        metadata={
            "semantic_id": "0173-1#02-AAO198#002",
        }
    )
    public_key: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO200#002",
        }
    )
    type_of_email_address: Optional[TypeOfEmailAddress] = field(metadata={"semantic_id": "0173-1#02-AAO199#003"})
    type_of_public_key: Optional[LangString] = field(metadata={"semantic_id": "0173-1#02-AAO201#002"})


@dataclass
class IPCommunication:
    address_of_additional_link: str = field(
        metadata={
            "semantic_id": "0173-1#02-AAQ326#002",
        }
    )
    type_of_communication: Optional[str] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/IPCommunication/TypeOfCommunication",
        }
    )
    available_time: Optional[str] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/",
        }
    )


@dataclass
class ContactInformation:
    role_of_contact_person: Optional[RoleOfContactPerson] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO204#003",
        }
    )
    national_code: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO134#002",
        }
    )
    language: Optional[List[str]] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Language",
        }
    )
    time_zone: Optional[str] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/TimeZone",
        }
    )
    # TODO: Add hint: "mandatory property according to EU MachineDirective 2006/42/EC."
    city_town: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO132#002",
        }
    )
    company: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAW001#001",
        }
    )
    department: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO127#003",
        }
    )
    phone: Optional[Phone] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Phone",
        }
    )
    fax: Optional[Fax] = field(
        metadata={
            "semantic_id": "0173-1#02-AAQ834#005",
        }
    )
    email: Optional[Email] = field(
        metadata={
            "semantic_id": "0173-1#02-AAQ836#005",
        }
    )
    ipc_communication: Optional[List[IPCommunication]] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/IPCommunication",
        }
    )
    street: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO128#002",
        }
    )
    zip_code: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO129#002",
        }
    )
    po_box: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO130#002",
        }
    )
    zip_code_of_po_box: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO131#002",
        }
    )
    state_country: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO133#002",
        }
    )
    name_of_contact: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO205#002",
        }
    )
    first_name: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO206#002",
        }
    )
    middle_name: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO207#002",
        }
    )
    title: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO208#003",
        }
    )
    academic_title: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO209#003",
        }
    )
    further_details_of_contact: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO210#002",
        }
    )
    address_of_additional_link: Optional[str] = field(
        metadata={
            "semantic_id": "] 0173-1#02-AAQ326#002",
        }
    )
    company_logo: Optional[str] = field(metadata={
        'semantic_id': '0112/2///61987#ABP463#001'
    })
    marking_file: str = field(metadata={
        'semantic_id': '0112/2///61987#ABO100#002'
    })


@dataclass
@template("https://exclusive/yulim.made")
class ContactInformations:
    contact_information: List[ContactInformation] = field(metadata={
        "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation",
    })
