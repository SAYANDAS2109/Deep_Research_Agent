from urllib.parse import urlparse


# ==========================================
# DOMAIN EXTRACTION
# ==========================================

def get_domain(url):

    try:

        domain = urlparse(
            url
        ).netloc.lower()

        domain = domain.replace(
            "www.",
            ""
        )

        return domain

    except Exception:

        return ""


# ==========================================
# SOURCE CLASSIFICATION
# ==========================================

def classify_source(url, title=""):

    domain = get_domain(url)

    # --------------------------------------
    # GOVERNMENT / OFFICIAL
    # --------------------------------------

    government_domains = (

        ".gov",

        ".gov.in",

        ".gov.uk",

        ".gov.au",

        ".gc.ca"
    )

    if domain.endswith(
        government_domains
    ):

        return {

            "source_type":
                "government",

            "quality_band":
                "high",

            "reason":
                "Government domain"
        }


    # --------------------------------------
    # ACADEMIC / EDUCATIONAL
    # --------------------------------------

    if (
        domain.endswith(".edu")
        or domain.endswith(".ac.uk")
        or domain.endswith(".ac.in")
    ):

        return {

            "source_type":
                "academic",

            "quality_band":
                "high",

            "reason":
                "Academic or educational domain"
        }


    # --------------------------------------
    # KNOWN RESEARCH / PUBLISHING DOMAINS
    # --------------------------------------

    academic_domains = {

        "sciencedirect.com",
        "springer.com",
        "nature.com",
        "wiley.com",
        "ieee.org",
        "acm.org",
        "arxiv.org",
        "researchgate.net",
        "oup.com",
        "tandfonline.com",
        "sagepub.com"
    }

    if domain in academic_domains:

        return {

            "source_type":
                "research_publisher",

            "quality_band":
                "high",

            "reason":
                "Recognized research/publishing platform"
        }


    # --------------------------------------
    # PETROLEUM / INDUSTRY ORGANIZATIONS
    # --------------------------------------

    industry_domains = {

        "spe.org",
        "onepetro.org",
        "slb.com",
        "halliburton.com",
        "bakerhughes.com",
        "bp.com",
        "shell.com",
        "chevron.com",
        "exxonmobil.com",
        "totalenergies.com"
    }

    if domain in industry_domains:

        return {

            "source_type":
                "industry",

            "quality_band":
                "medium-high",

            "reason":
                "Established petroleum or energy organization"
        }


    # --------------------------------------
    # NEWS / MEDIA
    # --------------------------------------

    news_domains = {

        "reuters.com",
        "bbc.com",
        "bbc.co.uk",
        "apnews.com",
        "nytimes.com",
        "theguardian.com",
        "ft.com"
    }

    if domain in news_domains:

        return {

            "source_type":
                "news",

            "quality_band":
                "medium",

            "reason":
                "Recognized news organization"
        }


    # --------------------------------------
    # UNKNOWN / GENERAL WEB
    # --------------------------------------

    return {

        "source_type":
            "general_web",

        "quality_band":
            "unknown",

        "reason":
            "Domain not classified by heuristic"
    }