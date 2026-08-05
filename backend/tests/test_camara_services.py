import pytest

from travelguard_ai.camara import CamaraClient, MockCamaraProvider
from travelguard_ai.camara.device_location import get_device_location_verification
from travelguard_ai.camara.location import get_location_verification
from travelguard_ai.camara.number_verification import get_number_verification
from travelguard_ai.camara.roaming import get_roaming_status
from travelguard_ai.camara.sim_swap import get_sim_swap_status


@pytest.mark.asyncio
async def test_location_service_function():
    client = CamaraClient(provider=MockCamaraProvider(seed=8))
    signal = await get_location_verification(client, ip_address="1.2.3.4", device_id="dev1", customer_country="US")
    assert signal.signal_name == "location"


@pytest.mark.asyncio
async def test_roaming_service_function():
    client = CamaraClient(provider=MockCamaraProvider(seed=9))
    signal = await get_roaming_status(client, ip_address="1.2.3.4", customer_country="US")
    assert signal.signal_name == "roaming"


@pytest.mark.asyncio
async def test_sim_swap_service_function():
    client = CamaraClient(provider=MockCamaraProvider(seed=10))
    signal = await get_sim_swap_status(client, customer_id="cust")
    assert signal.signal_name == "sim_swap"


@pytest.mark.asyncio
async def test_device_location_service_function():
    client = CamaraClient(provider=MockCamaraProvider(seed=11))
    signal = await get_device_location_verification(client, device_id="dev1", customer_country="US")
    assert signal.signal_name == "device_location"


@pytest.mark.asyncio
async def test_number_verification_service_function():
    client = CamaraClient(provider=MockCamaraProvider(seed=12))
    signal = await get_number_verification(client, phone_number="+212600000001")
    assert signal.signal_name == "number_verification"
