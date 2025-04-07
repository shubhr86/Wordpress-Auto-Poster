import requests
import base64

xml_rpc_url = "https://news47.us/xmlrpc.php"
username = "shubh861"
password = "3qE6 rhh0 UZgV 7tlW LaG3 CPwk"

data = """<?xml version="1.0"?>
<methodCall>
    <methodName>wp.getUsersBlogs</methodName>
    <params>
        <param><value><string>shubhr861</string></value></param>
        <param><value><string>3qE6 rhh0 UZgV 7tlW LaG3 CPwk</string></value></param>
    </params>
</methodCall>"""

# 🔹 Manually encode credentials (Base64)
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    "Content-Type": "text/xml",
    "Authorization": f"Basic {encoded_credentials}"  # 🔹 Explicitly set Basic Auth
}

response = requests.post(xml_rpc_url, data=data, headers=headers)

print("Response Code:", response.status_code)
print("Response Text:", response.text)
