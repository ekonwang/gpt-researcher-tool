
cd $(dirname $0)

python -m pip install -U certifi requests urllib3 idna charset-normalizer selenium
python -m pip install -r ./requirements_minimal.txt
python -m pip install -e .
