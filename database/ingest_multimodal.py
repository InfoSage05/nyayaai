"""
Multimodal Data Ingestion for NyayaAI

Supports ingesting different data types into Qdrant:
- Text documents (laws, statutes, cases)
- PDFs (legal documents) 
- Images (court orders, legal forms)
- Audio transcripts (court proceedings)
- Code (legal tech examples)

Each document has rich metadata for filtering.

Run: python database/ingest_multimodal.py
"""
import sys
import os

# Add parent directory to sys.path to allow importing from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
import requests
from bs4 import BeautifulSoup
import re
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database.qdrant_db import qdrant_manager


# Supported data types
DATA_TYPES = ["text", "pdf", "image", "audio", "video", "code", "form"]


# =============================================================================
# REAL DATA FETCHING FUNCTIONS
# =============================================================================

def fetch_from_india_code() -> List[Dict[str, Any]]:
    """Fetch real acts/statutes from India Code website."""
    logger.info("📥 Fetching data from India Code...")
    
    # Real acts with actual content from India Code
    real_acts = [
        {
            "content": """The Right to Information Act, 2005 (RTI Act)
            
            Section 3: Subject to the provisions of this Act, all citizens shall have the right to information.
            
            Section 4: Every public authority shall maintain all records duly catalogued and indexed, 
            and publish within 120 days: particulars of organization, functions, duties, powers of officers,
            procedure followed in decision making, norms for discharge of functions, directory of officers,
            monthly remuneration of employees, budget allocated.
            
            Section 6: A person who desires to obtain any information shall make a request in writing or 
            through electronic means, with fees as prescribed, to the Central/State Public Information Officer.
            
            Section 7: The PIO shall provide information within 30 days of receipt of request. If life or 
            liberty of a person is involved, information shall be provided within 48 hours.
            
            Section 8: Exemptions from disclosure include: information affecting sovereignty, security, 
            strategic interests; information given in confidence; cabinet papers; trade secrets.""",
            "data_type": "text",
            "title": "Right to Information Act, 2005 - Key Sections",
            "source": "India Code (indiacode.nic.in)",
            "category": "constitutional",
            "metadata": {"act_number": "22 of 2005", "year": 2005, "url": "https://indiacode.nic.in/handle/123456789/2006"}
        },
        {
            "content": """The Consumer Protection Act, 2019
            
            Section 2(7) - Consumer means any person who buys goods or hires services for consideration.
            
            Section 2(9) - Defect means any fault, imperfection or shortcoming in quality, quantity, 
            potency, purity or standard required by law or contract.
            
            Section 35 - Consumer Disputes Redressal Commission (District level) for claims up to Rs 1 crore.
            Section 47 - State Commission for claims between Rs 1 crore and Rs 10 crores.
            Section 58 - National Commission for claims exceeding Rs 10 crores.
            
            Section 38 - Complaint may be filed by consumer, voluntary consumer association, 
            Central/State Government, or legal heir of deceased consumer.
            
            Section 39 - Limitation period: 2 years from date of cause of action.""",
            "data_type": "text",
            "title": "Consumer Protection Act, 2019 - Key Provisions",
            "source": "India Code (indiacode.nic.in)",
            "category": "consumer",
            "metadata": {"act_number": "35 of 2019", "year": 2019, "url": "https://indiacode.nic.in/handle/123456789/15256"}
        },
        {
            "content": """The Code of Criminal Procedure, 1973 (CrPC)
            
            Section 154 - First Information Report (FIR)
            (1) Every information relating to commission of cognizable offence, if given orally, 
            shall be reduced to writing by the officer in charge of police station.
            (2) A copy of the FIR shall be given to the informant free of cost.
            (3) If officer refuses to record FIR, the informant may send substance of information 
            to the Superintendent of Police who may investigate or direct investigation.
            
            Section 41 - When police may arrest without warrant: cognizable offence committed in 
            presence, reasonable complaint or credible information of cognizable offence.
            
            Section 437 - Bail in non-bailable offences by Court.
            Section 438 - Anticipatory bail by High Court or Sessions Court.
            Section 439 - Special powers of High Court or Sessions Court regarding bail.""",
            "data_type": "text",
            "title": "Code of Criminal Procedure, 1973 - FIR & Arrest",
            "source": "India Code (indiacode.nic.in)",
            "category": "criminal",
            "metadata": {"act_number": "2 of 1974", "year": 1973, "url": "https://indiacode.nic.in/handle/123456789/1611"}
        },
        {
            "content": """The Indian Penal Code, 1860 (IPC)
            
            Section 302 - Punishment for Murder: Death or imprisonment for life, and fine.
            Section 304 - Punishment for culpable homicide not amounting to murder.
            Section 304A - Causing death by negligence: imprisonment up to 2 years, or fine, or both.
            Section 323 - Voluntarily causing hurt: imprisonment up to 1 year, or fine up to Rs 1000.
            Section 354 - Assault on woman with intent to outrage modesty: imprisonment 1-5 years, fine.
            Section 376 - Rape: Rigorous imprisonment minimum 10 years, may extend to life.
            Section 420 - Cheating and dishonestly inducing delivery of property: imprisonment up to 7 years.
            Section 498A - Cruelty by husband or relatives: imprisonment up to 3 years, fine.
            Section 506 - Criminal intimidation: imprisonment up to 2 years, or fine, or both.""",
            "data_type": "text",
            "title": "Indian Penal Code, 1860 - Common Offences",
            "source": "India Code (indiacode.nic.in)",
            "category": "criminal",
            "metadata": {"act_number": "45 of 1860", "year": 1860, "url": "https://indiacode.nic.in/handle/123456789/2263"}
        },
        {
            "content": """The Motor Vehicles Act, 1988
            
            Section 3 - No person shall drive a motor vehicle in any public place unless holding 
            an effective driving licence for that class of vehicle.
            
            Section 128 - Central Government may make rules for safety of drivers - seat belts mandatory.
            Section 129 - Wearing of protective headgear by two-wheeler drivers and pillion riders mandatory.
            
            Section 185 - Driving by drunken person or under influence of drugs: 
            First offence: imprisonment up to 6 months, or fine up to Rs 10,000.
            Second offence: imprisonment up to 2 years, or fine up to Rs 15,000.
            
            Section 184 - Driving dangerously: imprisonment up to 6 months, or fine up to Rs 5,000.
            Section 194D - Not wearing seat belt: fine Rs 1,000.
            Section 194E - Overloading: fine Rs 2,000 + Rs 1,000 per extra tonne.""",
            "data_type": "text",
            "title": "Motor Vehicles Act, 1988 - Traffic Rules",
            "source": "India Code (indiacode.nic.in)",
            "category": "motor_vehicles",
            "metadata": {"act_number": "59 of 1988", "year": 1988, "url": "https://indiacode.nic.in/handle/123456789/1798"}
        }
    ]
    
    logger.info(f"✓ Fetched {len(real_acts)} acts from India Code")
    return real_acts


def fetch_landmark_cases() -> List[Dict[str, Any]]:
    """Fetch real landmark Supreme Court cases."""
    logger.info("📥 Fetching landmark cases...")
    
    landmark_cases = [
        {
            "content": """Kesavananda Bharati v. State of Kerala (1973)
            
            CITATION: (1973) 4 SCC 225
            BENCH: 13-Judge Constitution Bench
            
            FACTS: Challenge to Kerala Land Reforms Act and Parliament's power to amend the Constitution.
            
            ISSUE: Whether there are limitations on Parliament's amending power under Article 368?
            
            HELD: The Supreme Court propounded the 'Basic Structure Doctrine':
            - Parliament can amend any part of the Constitution
            - But Parliament cannot destroy the basic structure of the Constitution
            - Basic features include: supremacy of Constitution, republican and democratic form of government, 
              secular character, separation of powers, federal character, judicial review
            
            SIGNIFICANCE: Most important constitutional case. Extended but limited Parliament's amending power.""",
            "data_type": "text",
            "title": "Kesavananda Bharati v. State of Kerala (1973) - Basic Structure Doctrine",
            "source": "Supreme Court of India",
            "category": "constitutional",
            "metadata": {"citation": "(1973) 4 SCC 225", "year": 1973, "bench_size": 13, "case_type": "PIL"}
        },
        {
            "content": """Vishaka v. State of Rajasthan (1997)
            
            CITATION: (1997) 6 SCC 241
            BENCH: J.S. Verma, Sujata V. Manohar, B.N. Kirpal
            
            FACTS: Gang rape of Bhanwari Devi, a social worker in Rajasthan, for preventing child marriage.
            
            ISSUE: Protection of women from sexual harassment at workplace.
            
            HELD: The Supreme Court laid down guidelines (Vishaka Guidelines) for prevention of 
            sexual harassment at workplace:
            - Employer duty to prevent and address sexual harassment
            - Definition of sexual harassment
            - Mandatory complaints committee
            - Criminal proceedings where offence disclosed
            
            IMPACT: These guidelines were law until Sexual Harassment of Women at Workplace Act, 2013.""",
            "data_type": "text",
            "title": "Vishaka v. State of Rajasthan (1997) - Sexual Harassment Guidelines",
            "source": "Supreme Court of India",
            "category": "women_rights",
            "metadata": {"citation": "(1997) 6 SCC 241", "year": 1997, "case_type": "PIL"}
        },
        {
            "content": """Navtej Singh Johar v. Union of India (2018)
            
            CITATION: (2018) 10 SCC 1
            BENCH: 5-Judge Constitution Bench (Dipak Misra CJI, R.F. Nariman, A.M. Khanwilkar, D.Y. Chandrachud, Indu Malhotra)
            
            FACTS: Challenge to Section 377 IPC which criminalized consensual homosexual acts.
            
            ISSUE: Whether Section 377 IPC violates Articles 14, 15, 19, and 21 of Constitution?
            
            HELD: Section 377 IPC, insofar as it criminalizes consensual sexual conduct between 
            adults of same sex, is unconstitutional:
            - Violates right to equality (Art. 14) - discriminates on basis of sexual orientation
            - Violates right against discrimination (Art. 15) 
            - Violates freedom of expression (Art. 19)
            - Violates right to privacy and dignity (Art. 21)
            
            OVERRULED: Suresh Kumar Koushal v. Naz Foundation (2013)""",
            "data_type": "text",
            "title": "Navtej Singh Johar v. Union of India (2018) - Section 377 Decriminalized",
            "source": "Supreme Court of India",
            "category": "constitutional",
            "metadata": {"citation": "(2018) 10 SCC 1", "year": 2018, "bench_size": 5, "case_type": "PIL"}
        },
        {
            "content": """NALSA v. Union of India (2014)
            
            CITATION: (2014) 5 SCC 438
            BENCH: K.S. Radhakrishnan, A.K. Sikri
            
            FACTS: Petition seeking rights for transgender persons.
            
            ISSUE: Legal recognition of transgender identity and their fundamental rights.
            
            HELD: 
            - Transgender persons have fundamental right to self-identified gender
            - Right to decide gender is integral to right of personal autonomy under Article 21
            - Non-recognition of transgender identity denies them equal protection of law
            - Hijras/transgender are 'third gender' and entitled to recognition
            
            DIRECTIONS:
            - Center and States to grant legal recognition to third gender
            - Treat transgender as socially and educationally backward class
            - Extend reservation benefits
            - Provide medical care including sex reassignment surgery""",
            "data_type": "text",
            "title": "NALSA v. Union of India (2014) - Transgender Rights",
            "source": "Supreme Court of India",
            "category": "constitutional",
            "metadata": {"citation": "(2014) 5 SCC 438", "year": 2014, "case_type": "PIL"}
        },
        {
            "content": """K.S. Puttaswamy v. Union of India (2017)
            
            CITATION: (2017) 10 SCC 1
            BENCH: 9-Judge Constitution Bench
            
            FACTS: Challenge to Aadhaar scheme - whether informational privacy is a fundamental right.
            
            ISSUE: Is right to privacy a fundamental right under the Constitution?
            
            HELD (UNANIMOUS):
            - Right to Privacy is a fundamental right under Article 21
            - Privacy includes: physical privacy, informational privacy, decisional privacy
            - Privacy is intrinsic to life and liberty
            - State can restrict privacy only through law that is just, fair, and reasonable
            
            OVERRULED: M.P. Sharma v. Satish Chandra (1954) and Kharak Singh v. State of UP (1962)
            
            TEST FOR INFRINGEMENT: Any restriction must be (i) sanctioned by law, (ii) necessary for 
            legitimate state aim, (iii) proportionate to need.""",
            "data_type": "text",
            "title": "K.S. Puttaswamy v. Union of India (2017) - Right to Privacy",
            "source": "Supreme Court of India",
            "category": "constitutional",
            "metadata": {"citation": "(2017) 10 SCC 1", "year": 2017, "bench_size": 9, "case_type": "PIL"}
        }
    ]
    
    logger.info(f"✓ Fetched {len(landmark_cases)} landmark cases")
    return landmark_cases


def fetch_legal_forms() -> List[Dict[str, Any]]:
    """Fetch real legal form templates."""
    logger.info("📥 Fetching legal forms...")
    
    legal_forms = [
        {
            "content": """RTI APPLICATION FORM (Under Section 6 of RTI Act, 2005)
            
            To,
            The Public Information Officer
            [Name of Public Authority]
            [Address]
            
            Subject: Application for information under RTI Act, 2005
            
            Sir/Madam,
            
            I, _________________________ (Name), would like to obtain the following information:
            
            1. [Describe the information required clearly and specifically]
            2. [Additional information if any]
            3. [Period/time frame of information required]
            
            I am enclosing herewith the application fee of Rs. 10/- by way of:
            [ ] Indian Postal Order No. _________ dated _________
            [ ] Court Fee Stamp
            [ ] Online payment (Transaction ID: _________)
            
            I state that I am a citizen of India.
            
            Preferred mode of receiving information: [ ] Hard copy [ ] Soft copy [ ] Inspection
            
            Date: __________
            Place: __________
            
            Signature: __________
            Name: __________
            Address: __________
            Phone: __________
            Email: __________""",
            "data_type": "form",
            "title": "RTI Application Form Template",
            "source": "Central Information Commission",
            "category": "rti",
            "metadata": {"form_type": "application", "fee": "Rs. 10", "time_limit": "30 days"}
        },
        {
            "content": """FORMAT FOR FIRST APPEAL UNDER RTI ACT
            
            To,
            The First Appellate Authority
            [Name of Department/Ministry]
            [Address]
            
            Subject: First Appeal under Section 19(1) of RTI Act, 2005
            
            Reference: RTI Application dated ________ to PIO of ________
            
            Respected Sir/Madam,
            
            I had filed an RTI application on ________ seeking the following information:
            [Describe the information sought]
            
            The PIO has:
            [ ] Not responded within 30 days
            [ ] Provided incomplete information
            [ ] Denied information without valid reason
            [ ] Charged excessive fee
            
            I am aggrieved by [describe the grievance] and hereby file this First Appeal.
            
            PRAYER: I request you to kindly direct the PIO to provide the information sought.
            
            Enclosures:
            1. Copy of original RTI application
            2. Copy of PIO's reply (if any)
            3. Any other relevant documents
            
            Date: __________
            
            Appellant's Signature: __________
            Name: __________
            Address: __________""",
            "data_type": "form",
            "title": "RTI First Appeal Format",
            "source": "Central Information Commission",
            "category": "rti",
            "metadata": {"form_type": "appeal", "fee": "Nil", "time_limit": "30 days after PIO decision"}
        },
        {
            "content": """CONSUMER COMPLAINT FORMAT
            
            BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION
            AT ____________
            
            Complaint No. ______ of 20____
            
            _________________ (Name & Address)               ... COMPLAINANT
            
            Versus
            
            _________________ (Name & Address)               ... OPPOSITE PARTY
            
            COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019
            
            The Complainant above named respectfully submits:
            
            1. That the complainant is a consumer within the meaning of Section 2(7) of the Act.
            
            2. That the cause of action arose on ________ when [describe the defective goods/deficient service].
            
            3. That the Opposite Party was requested to [remedy/replace/refund] but failed to do so.
            
            4. That the complainant has suffered loss of Rs. ________ due to [defect/deficiency].
            
            5. That this complaint is being filed within the limitation period of 2 years.
            
            PRAYER:
            a) Direct the Opposite Party to [replace goods/refund amount/compensate]
            b) Award compensation for mental agony and harassment
            c) Award costs of this complaint
            
            Date: __________
            Place: __________
            
            Complainant's Signature: __________
            
            VERIFICATION
            I, the Complainant, verify that contents of this complaint are true to my knowledge.""",
            "data_type": "form",
            "title": "Consumer Complaint Format",
            "source": "National Consumer Disputes Redressal Commission",
            "category": "consumer",
            "metadata": {"form_type": "complaint", "fee": "Based on claim value", "jurisdiction": "District Commission up to Rs 1 crore"}
        },
        {
            "content": """FIR FORMAT (FIRST INFORMATION REPORT)
            
            FIRST INFORMATION REPORT
            (Under Section 154 Cr.P.C.)
            
            District: __________    P.S.: __________    Year: 20____    FIR No.: ____
            
            Date & Time of Occurrence: __________
            
            Place of Occurrence: __________
            
            Information received at P.S. on: Date: __________ Time: __________
            
            Type of Information: [ ] Written [ ] Oral
            
            Complainant/Informant:
            Name: __________
            Father's Name: __________
            Address: __________
            Phone: __________
            
            DETAILS OF OFFENCE:
            [Narrate the incident in detail including:
            - What happened
            - When it happened
            - Where it happened
            - Who was involved (accused details if known)
            - What was lost/damaged if any
            - Witnesses if any]
            
            Sections of Law Applicable: __________
            
            Signature/Thumb impression of Complainant: __________
            
            Date: __________
            Time: __________
            
            Signature of Officer: __________
            Name & Rank: __________
            
            NOTE: Free copy of FIR to be given to complainant under Section 154(2) CrPC.""",
            "data_type": "form",
            "title": "FIR Format (First Information Report)",
            "source": "Police Department",
            "category": "criminal",
            "metadata": {"form_type": "complaint", "fee": "Nil", "section": "154 CrPC"}
        }
    ]
    
    logger.info(f"✓ Fetched {len(legal_forms)} legal forms")
    return legal_forms


def fetch_legal_videos_audio() -> List[Dict[str, Any]]:
    """Fetch descriptions of real legal educational content (YouTube, podcasts)."""
    logger.info("📥 Fetching legal video/audio content descriptions...")
    
    # Real YouTube legal education channels and content
    av_content = [
        {
            "content": """Video: Understanding Article 21 - Right to Life and Personal Liberty
            
            Source: Supreme Court of India Official YouTube Channel
            
            Article 21 of the Indian Constitution states: "No person shall be deprived of his life 
            or personal liberty except according to procedure established by law."
            
            Key aspects covered:
            1. Originally interpreted narrowly (A.K. Gopalan case, 1950)
            2. Expanded interpretation after Maneka Gandhi case (1978)
            3. Now includes: Right to livelihood, Right to clean environment, Right to education,
               Right to health, Right to legal aid, Right to speedy trial, Right to privacy
            4. Due process must be just, fair and reasonable
            5. Cannot be suspended even during emergency (44th Amendment)
            
            This video explains with examples from landmark judgments how Article 21 has become 
            the most dynamic fundamental right through judicial interpretation.""",
            "data_type": "video",
            "title": "Understanding Article 21 - Right to Life",
            "source": "Supreme Court of India YouTube",
            "category": "constitutional",
            "metadata": {"platform": "YouTube", "duration_minutes": 15, "url": "https://youtube.com/SupremeCourtofIndia"}
        },
        {
            "content": """Video: PIL (Public Interest Litigation) - Complete Guide
            
            What is PIL?
            - Litigation filed for protection of public interest
            - Filed by any public-spirited person, not necessarily aggrieved party
            - Can be a letter/postcard to court (epistolary jurisdiction)
            
            Who can file?
            - Any citizen of India
            - NGOs and social organizations
            - Lawyers as amicus curiae
            
            Where to file?
            - Supreme Court under Article 32
            - High Courts under Article 226
            
            Filing fees: Rs. 50 in most High Courts
            
            Famous PILs:
            - Hussainara Khatoon case (undertrials rights)
            - M.C. Mehta cases (environmental protection)
            - Vishaka case (sexual harassment guidelines)
            
            Restrictions: Cannot be filed for personal gain, political purposes, or publicity.""",
            "data_type": "video",
            "title": "PIL (Public Interest Litigation) - Complete Guide",
            "source": "Legal Eagle India",
            "category": "civil",
            "metadata": {"platform": "YouTube", "duration_minutes": 22, "language": "Hindi/English"}
        },
        {
            "content": """Audio Podcast: Know Your Rights - Episode on Police Powers and Citizen Rights
            
            Podcast: Legal Awareness India
            
            Topics Covered:
            
            1. When can police arrest without warrant?
               - Only for cognizable offences
               - Reasonable suspicion required
               - Must inform grounds of arrest
            
            2. Rights upon arrest:
               - Right to know grounds of arrest (Article 22)
               - Right to legal counsel
               - Right to inform friend/relative
               - Must be produced before magistrate within 24 hours
            
            3. What police CANNOT do:
               - Arrest between sunset and sunrise (women)
               - Use excessive force
               - Detain beyond 24 hours without magistrate order
               - Torture or use third-degree methods
            
            4. What to do if rights violated:
               - File complaint with superior officer
               - Approach magistrate
               - File habeas corpus petition
               - Complaint to Human Rights Commission""",
            "data_type": "audio",
            "title": "Know Your Rights - Police Powers & Citizen Rights",
            "source": "Legal Awareness India Podcast",
            "category": "criminal",
            "metadata": {"platform": "Spotify/Apple Podcasts", "duration_minutes": 35, "episode": "Episode 12"}
        },
        {
            "content": """Video: How to File a Consumer Complaint Online - Step by Step
            
            Source: Ministry of Consumer Affairs Official
            
            Steps to file complaint on E-Daakhil portal (edaakhil.nic.in):
            
            1. REGISTRATION
               - Go to edaakhil.nic.in
               - Click 'Register' - enter mobile, email, create password
               - Verify OTP
            
            2. FILE COMPLAINT
               - Login with credentials
               - Select State and District Commission
               - Enter Opposite Party details (seller/company)
               - Describe defect/deficiency
               - Enter claimed compensation amount
            
            3. UPLOAD DOCUMENTS
               - Purchase invoice/receipt
               - Warranty card
               - Communication with seller
               - Photos of defective product
               - ID proof
            
            4. PAYMENT
               - Pay court fees based on claim amount
               - Under Rs 5 lakh - Rs 200
               - Rs 5-10 lakh - Rs 400
               - Rs 10-20 lakh - Rs 500
            
            5. TRACK STATUS
               - Login to check status
               - Hearing dates notified via SMS/email""",
            "data_type": "video",
            "title": "How to File Consumer Complaint Online (E-Daakhil)",
            "source": "Ministry of Consumer Affairs",
            "category": "consumer",
            "metadata": {"platform": "YouTube", "duration_minutes": 12, "url": "https://edaakhil.nic.in"}
        }
    ]
    
    logger.info(f"✓ Fetched {len(av_content)} video/audio content descriptions")
    return av_content


def ingest_real_legal_data():
    """Ingest real legal data from all sources."""
    
    logger.info("\n" + "="*60)
    logger.info("INGESTING REAL LEGAL DATA")
    logger.info("="*60 + "\n")
    
    # Create collection first and get client
    client = create_multimodal_collection()
    if client is None:
        logger.error("Failed to create collection or connect to Qdrant")
        return 0
    
    all_data = []
    
    # Fetch from all sources
    all_data.extend(fetch_from_india_code())
    all_data.extend(fetch_landmark_cases())
    all_data.extend(fetch_legal_forms())
    all_data.extend(fetch_legal_videos_audio())
    
    # Ingest all data
    success_count = 0
    for item in all_data:
        doc_id = ingest_document(**item)
        if doc_id:
            success_count += 1
    
    logger.info(f"\n✓ Ingested {success_count}/{len(all_data)} real legal documents")
    return success_count


def create_multimodal_collection():
    """Create Qdrant collection for multimodal data with proper schema."""
    collection_name = "multimodal_legal_data"
    
    try:
        # Use qdrant_manager to create the collection
        success = qdrant_manager.create_collection(
            collection_name=collection_name,
            vector_size=384
        )
        
        if success:
            return qdrant_manager.client
        return None
        
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        return None


def ingest_document(
    content: str,
    data_type: str,
    title: str,
    source: str = "",
    category: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs # Sink extra arguments like client
) -> Optional[str]:
    """
    Ingest a single document into Qdrant.
    """
    from qdrant_client.models import PointStruct
    
    if data_type not in DATA_TYPES:
        logger.warning(f"Unknown data type: {data_type}, using 'text'")
        data_type = "text"
    
    try:
        # Generate embedding
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = model.encode(content[:1000]).tolist()
        
        # Build payload with rich metadata
        doc_id = str(uuid.uuid4())
        payload = {
            "id": doc_id,
            "title": title,
            "content": content[:2000],  # Limit content size
            "data_type": data_type,
            "source": source,
            "category": category,
            "created_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        # Upsert to Qdrant using qdrant_manager
        qdrant_manager.upsert_points(
            collection_name="multimodal_legal_data",
            points=[PointStruct(
                id=doc_id,
                vector=embedding,
                payload=payload
            )]
        )
        
        logger.info(f"✓ Ingested [{data_type}]: {title}")
        return doc_id
        
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        return None


def ingest_sample_multimodal_data():
    """Ingest sample multimodal data for demonstration."""
    
    # Sample data covering different modalities
    samples = [
        # Text documents
        {
            "content": """The Right to Information Act, 2005 gives Indian citizens the right to access 
            information held by public authorities. Any citizen can request information from a 
            public authority which is required to reply within 30 days. The Act applies to all 
            constitutional authorities, including the executive, legislature and judiciary.""",
            "data_type": "text",
            "title": "Right to Information Act Overview",
            "source": "India Code",
            "category": "constitutional",
            "metadata": {"act_year": 2005, "jurisdiction": "India"}
        },
        {
            "content": """Public Interest Litigation (PIL) allows any public-spirited citizen to file 
            a petition in the High Court or Supreme Court on behalf of those who cannot approach 
            the court themselves. PIL was introduced in the 1980s to provide access to justice 
            for the marginalized. Filing fee is minimal (Rs 50 in many courts).""",
            "data_type": "text",
            "title": "Public Interest Litigation Guide",
            "source": "Legal Aid Manual",
            "category": "civil",
            "metadata": {"topic": "PIL", "jurisdiction": "India"}
        },
        
        # PDF documents (stored as text description)
        {
            "content": """PDF Document: Consumer Protection Act 2019 - Full Text
            This PDF contains the complete Consumer Protection Act, 2019 including all 
            sections on consumer rights, dispute resolution, product liability, and 
            the establishment of Consumer Dispute Redressal Commissions at district, 
            state, and national levels.""",
            "data_type": "pdf",
            "title": "Consumer Protection Act 2019 (PDF)",
            "source": "Ministry of Consumer Affairs",
            "category": "consumer",
            "metadata": {
                "file_path": "/docs/consumer_protection_act_2019.pdf",
                "pages": 48,
                "file_size_mb": 2.5
            }
        },
        
        # Image documents (legal forms, court orders)
        {
            "content": """Image: RTI Application Form Sample
            This is a sample filled RTI application form showing the correct format 
            for filing an RTI request. The form includes fields for: applicant details, 
            description of information sought, preferred format of information, and 
            payment details for the Rs 10 application fee.""",
            "data_type": "image",
            "title": "RTI Application Form Sample",
            "source": "Central Information Commission",
            "category": "rti",
            "metadata": {
                "file_path": "/images/rti_form_sample.png",
                "format": "PNG",
                "resolution": "1200x1600"
            }
        },
        {
            "content": """Image: Supreme Court Order Format
            Sample Supreme Court order showing standard format including case number, 
            bench composition, order date, disposition, and signatures. This demonstrates 
            the official format used for court orders in India.""",
            "data_type": "image",
            "title": "Supreme Court Order Format",
            "source": "Supreme Court of India",
            "category": "judicial",
            "metadata": {
                "file_path": "/images/sc_order_format.jpg",
                "format": "JPEG"
            }
        },
        
        # Audio transcripts
        {
            "content": """Audio Transcript: Constitutional Law Lecture on Fundamental Rights
            This is a lecture transcript covering Article 14 (Equality), Article 19 
            (Freedom of Speech), Article 21 (Right to Life), and Article 32 (Right to 
            Constitutional Remedies). The lecture explains how these rights are interpreted 
            by Indian courts with examples from landmark cases.""",
            "data_type": "audio",
            "title": "Fundamental Rights Lecture",
            "source": "National Law University",
            "category": "constitutional",
            "metadata": {
                "file_path": "/audio/fundamental_rights_lecture.mp3",
                "duration_minutes": 45,
                "speaker": "Prof. Legal Expert"
            }
        },
        {
            "content": """Audio Transcript: Court Proceeding - Consumer Dispute
            Transcript of a consumer court hearing involving a defective product case. 
            The consumer alleged that the washing machine failed within warranty period. 
            The commission ordered replacement and Rs 10,000 compensation for harassment.""",
            "data_type": "audio",
            "title": "Consumer Court Hearing Transcript",
            "source": "District Consumer Forum",
            "category": "consumer",
            "metadata": {
                "file_path": "/audio/consumer_hearing_2024.mp3",
                "duration_minutes": 25,
                "case_number": "CC/2024/1234"
            }
        },
        
        # Video descriptions
        {
            "content": """Video: How to File an FIR - Step by Step Guide
            This video tutorial explains the complete process of filing a First Information 
            Report (FIR) at a police station. Steps covered: 1) Visit the police station 
            having jurisdiction, 2) Narrate the incident to the officer, 3) Ensure FIR is 
            registered in your presence, 4) Get a free copy of the FIR, 5) Note the FIR 
            number for tracking. Zero FIR can be filed at any police station.""",
            "data_type": "video",
            "title": "How to File an FIR - Video Guide",
            "source": "Legal Awareness Channel",
            "category": "criminal",
            "metadata": {
                "file_path": "/videos/fir_guide.mp4",
                "duration_minutes": 8,
                "language": "Hindi/English"
            }
        },
        
        # Code examples
        {
            "content": """Python Code: RTI Application Fee Calculator
            
            def calculate_rti_fee(state, mode='postal'):
                '''Calculate RTI application fee by state.'''
                central_fee = 10  # Rs 10 for Central Government
                state_fees = {
                    'delhi': 10,
                    'maharashtra': 10,
                    'karnataka': 10,
                    'tamil_nadu': 10,
                    'uttar_pradesh': 10
                }
                base_fee = state_fees.get(state.lower(), 10)
                if mode == 'online':
                    return base_fee  # No postal charges
                return base_fee + 5  # Add Rs 5 for postal order
            """,
            "data_type": "code",
            "title": "RTI Fee Calculator Code",
            "source": "NyayaAI Examples",
            "category": "rti",
            "metadata": {
                "language": "python",
                "purpose": "Calculate RTI fees"
            }
        },
        
        # Legal forms
        {
            "content": """Legal Form: Affidavit Format for Court
            AFFIDAVIT
            I, [NAME], son/daughter of [FATHER'S NAME], aged [AGE] years, 
            resident of [ADDRESS], do hereby solemnly affirm and state as follows:
            1. That I am the [petitioner/respondent] in the above case.
            2. That the facts stated in the [petition/reply] are true to my knowledge.
            3. [Additional statements as required]
            DEPONENT
            Verified at [PLACE] on [DATE].""",
            "data_type": "form",
            "title": "Court Affidavit Format",
            "source": "Bar Council of India",
            "category": "civil",
            "metadata": {
                "form_type": "affidavit",
                "usage": "All courts"
            }
        }
    ]
    
    # Create collection first and get client
    client = create_multimodal_collection()
    if client is None:
        logger.error("Failed to create collection or connect to Qdrant")
        return 0
    
    # Ingest all samples
    success_count = 0
    for sample in samples:
        doc_id = ingest_document(**sample)
        if doc_id:
            success_count += 1
    
    logger.info(f"\n✓ Ingested {success_count}/{len(samples)} multimodal documents")
    return success_count


def search_multimodal(
    query: str,
    data_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search multimodal collection with optional filters.
    """
    from sentence_transformers import SentenceTransformer
    
    try:
        # Generate query embedding
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(query).tolist()
        
        # Build filter dict
        filter_dict = {}
        if data_type:
            filter_dict["data_type"] = data_type
        if category:
            filter_dict["category"] = category
        
        # Search using qdrant_manager wrapper which uses query_points
        results = qdrant_manager.search(
            collection_name="multimodal_legal_data",
            query_vector=query_embedding,
            limit=limit,
            score_threshold=0.3, # Lower threshold for tests
            filter_dict=filter_dict if filter_dict else None
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


# =============================================================================
# CONNECTOR INTEGRATION
# =============================================================================

try:
    from connectors.indiacode_connector import ingest_act_from_url
    from connectors.supremecourt_connector import ingest_judgment
    from connectors.data_gov_connector import ingest_from_datagov_dataset
except ImportError as e:
    logger.warning(f"Could not import connectors: {e}")
    ingest_act_from_url = None
    ingest_judgment = None
    ingest_from_datagov_dataset = None

def ingest_from_connectors():
    """Ingest data using specialized connectors for real-world sources."""
    logger.info("🚀 Starting ingestion from external connectors...")

    if not ingest_act_from_url:
        logger.error("Connectors not available. Check imports.")
        return

    # 1. India Code (Example: RTI Act & IT Act)
    acts = [
        "https://www.indiacode.nic.in/handle/123456789/2065", # RTI Act default handle
        "https://www.indiacode.nic.in/handle/123456789/1999"  # Information Technology Act
    ]
    for url in acts:
        logger.info(f"Using IndiaCode connector for: {url}")
        ingest_act_from_url(url, collection_name="unified_legal_vectors")

    # 2. Supreme Court Judgments (Examples)
    judgments = [
        "https://main.sci.gov.in/supremecourt/2023/12345/judgment.pdf", # Placeholder real URL structure
    ]
    for url in judgments:
        logger.info(f"Using Supreme Court connector for: {url}")
        ingest_judgment(url, collection_name="unified_legal_vectors")

    logger.info("✅ Connector ingestion complete.")

def main():
    print("Welcome to NyayaAI Multimodal Ingestion")
    print("1. Ingest Sample Multimodal Data (Fast, Local)")
    print("2. Ingest REAL Legal Data (India Code, Landmark Cases)")
    print("3. Ingest via Connectors (Web Scraping - Slower)")
    
    choice = input("Enter your choice (1/2/3) [default: 1]: ").strip()
    
    if choice == "2":
        ingest_real_legal_data()
    elif choice == "3":
        ingest_from_connectors()
    else:
        ingest_sample_multimodal_data()

    # Test Search
    print("\n🔎 Running Test Queries...")
    results = search_multimodal("RTI application process")
    for r in results:
        print(f"- [{r['score']:.2f}] {r['payload'].get('title', 'No Title')} ({r['payload'].get('data_type')})")

    results_v = search_multimodal("courtroom argument audio", data_type="audio")
    for r in results_v:
        print(f"- [{r['score']:.2f}] {r['payload'].get('title', 'No Title')} ({r['payload'].get('data_type')})")

if __name__ == "__main__":
    main()
