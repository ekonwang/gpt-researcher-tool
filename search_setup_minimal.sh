# if ! conda env list | grep -q "gpt-researcher"; then
#     print_step "Creating conda environment 'gpt-researcher' with Python 3.11..."
#     conda create -n gpt-researcher python==3.11 -y
# else
#     print_step "Conda environment 'gpt-researcher' already exists"
# fi

# eval "$(conda shell.bash hook)"
# conda activate gpt-researcher

cd $(dirname $0)

# python3 -m pip install -U certifi requests urllib3 idna charset-normalizer selenium
# python3 -m pip install -r ./requirements_minimal.txt
python3 -m pip install -e .

python3 -m pip install click==8.2.1 tokenizers==0.21 numpy==1.26.4
pip3 install autogen
