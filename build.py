import os
import shutil
import subprocess
import tempfile
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DEPLOYMENTS_DIR = os.path.join(BASE_DIR, 'terraform', 'deployments')


def parse_folders_to_zip_config(config_file):
    """Lê o arquivo de configuração e retorna um dicionário com diretórios e pastas."""
    folders_to_process = []
    with open(config_file, 'r', encoding='utf-8') as f:
        current_dir = None
        for line in f:
            line = line.strip()
            if line.startswith('DIR ='):
                current_dir = line.split('=')[1].strip()
            elif line.startswith('FOLDERS_TO_ZIP =') and current_dir:
                folders = line.split('=')[1].strip().split(',')
                folders = [folder.strip() for folder in folders]
                for folder in folders:
                    folders_to_process.append((current_dir, folder))
    return folders_to_process


def find_requirements_file(folder_path):
    """Procura por arquivos .txt com 'requirements' no nome dentro da pasta especificada."""
    for root, _, files in os.walk(folder_path):
        for file in files:
            if 'requirements' in file.lower() and file.endswith('.txt'):
                return os.path.join(root, file)
    return None


def install_dependencies_to_temp(source_path, temp_dir):
    """Instala as dependências em um diretório temporário."""
    requirements_file = find_requirements_file(source_path)

    if requirements_file:
        print(f"Instalando dependências para {source_path} (arquivo encontrado: {requirements_file})...")
        try:
            subprocess.run(
                [
                    'pip3', 'install', '-r', requirements_file,
                    '--platform', 'manylinux2014_x86_64',
                    '--target', temp_dir,
                    '--only-binary=:all:',
                    '--upgrade'
                ],
                check=True
            )
            print(f"[SUCESSO] Dependências instaladas em pasta temporária para {source_path}.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao instalar dependências para {source_path}: {e}")
    else:
        print(f"[AVISO] Nenhum arquivo de requisitos encontrado em {source_path}.")


def adjust_imports(folder_path, base_module):
    """Ajusta importações removendo o prefixo do módulo base, apenas em arquivos que precisam."""
    print(f"Ajustando importações na pasta: {folder_path}")
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Verifica se o módulo base aparece no conteúdo
                    if base_module in content:
                        updated_content = re.sub(
                            rf'\b{re.escape(base_module)}\.',
                            '',
                            content
                        )
                        # Sobrescreve o arquivo apenas se houve alteração
                        if updated_content != content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            print(f"Importações ajustadas em: {file_path}")
                except UnicodeDecodeError as e:
                    print(f"[ERRO] Falha ao processar {file_path}: {e}")


def create_zip(base_dir, folder_name):
    """Cria o arquivo ZIP da Lambda."""
    source_path = os.path.join(BASE_DIR, base_dir, folder_name)
    zip_path = os.path.join(DEPLOYMENTS_DIR, f"{folder_name}.zip")

    if not os.path.exists(source_path):
        print(f"[ERRO] Pasta não encontrada: {source_path}")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        # Copia o conteúdo original para o diretório temporário
        temp_source = os.path.join(temp_dir, folder_name)
        shutil.copytree(source_path, temp_source)

        # Instala as dependências no diretório temporário
        install_dependencies_to_temp(source_path, temp_source)

        # Ajusta importações no diretório temporário
        base_module = f"{base_dir}.{folder_name}".replace('/', '.')
        adjust_imports(temp_source, base_module)

        # Cria o ZIP a partir do diretório temporário
        shutil.make_archive(base_name=zip_path.replace('.zip', ''), format='zip', root_dir=temp_source)
        print(f"[SUCESSO] Arquivo ZIP criado: {zip_path}")


# Garante que o diretório de destino existe
if not os.path.exists(DEPLOYMENTS_DIR):
    os.makedirs(DEPLOYMENTS_DIR)

# Lê as configurações do arquivo
config_file_path = os.path.join(BASE_DIR, 'folders_to_zip')
folders_to_process = parse_folders_to_zip_config(config_file_path)

# Processa cada pasta conforme a configuração
for base_dir, folder in folders_to_process:
    create_zip(base_dir, folder)
