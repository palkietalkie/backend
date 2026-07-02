from app.services.openai.constants import OPENAI_REALTIME_CALLS_URL_TEMPLATE


def test_calls_url_template_builds_the_realtime_calls_endpoint() -> None:
    # The WebRTC path POSTs its SDP offer to this URL; the path + model query must be exact or the handshake 404s.
    url = OPENAI_REALTIME_CALLS_URL_TEMPLATE.format(model="gpt-realtime-2")
    assert url == "https://api.openai.com/v1/realtime/calls?model=gpt-realtime-2"
