import requests


def verify_pincode(pincode, entered_city, entered_state):
    """
    Verifies a pincode against India Post's public API.
    Returns a dict: {"valid": bool, "warning": str or None, "error": str or None}
    """
    if not pincode or not pincode.isdigit() or len(pincode) != 6:
        return {"valid": False, "warning": None, "error": "Pincode must be exactly 6 digits."}

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}", headers=headers, timeout=10)        
        data = response.json()
    except Exception as e:
        # If the API is unreachable, don't hard-block the user — just skip verification.
        print(f"⚠️ Pincode API unreachable: {e}")
        return {"valid": True, "warning": "Could not verify pincode online — proceeding unverified.", "error": None}

    if not data or data[0].get("Status") != "Success":
        return {"valid": False, "warning": None, "error": "This pincode does not exist."}

    post_offices = data[0].get("PostOffice", [])
    if not post_offices:
        return {"valid": False, "warning": None, "error": "This pincode does not exist."}

    registered_states = {po["State"].strip().lower() for po in post_offices}
    registered_districts = {po["District"].strip().lower() for po in post_offices}

    if entered_state.strip().lower() not in registered_states:
        return {
            "valid": False,
            "warning": None,
            "error": f"This pincode belongs to {list(registered_states)[0].title()}, not {entered_state}.",
        }

    if entered_city.strip().lower() not in registered_districts:
        return {
            "valid": True,
            "warning": f"Note: this pincode's registered district is '{list(registered_districts)[0].title()}' — double check your city if that looks wrong.",
            "error": None,
        }

    return {"valid": True, "warning": None, "error": None}