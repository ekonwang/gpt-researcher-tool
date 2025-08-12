# 保证证书不过期
export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
export GOOGLE_API_KEY=AIzaSyBdIPo8M_NI4jlwCGi9wmNPz6moTRBk42E
export GOOGLE_CX_KEY=2509d50569c33464b

# google apis 测试
python -c 'import os,requests; print(os.getenv("ALL_PROXY")); print(requests.get("https://www.googleapis.com/", timeout=15).status_code)'

# 测试
python -m gpt_researcher.search_worker --query "starry night" --retriever google --max_results 3
