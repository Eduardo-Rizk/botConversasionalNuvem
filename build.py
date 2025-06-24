import os
import shutil
import subprocess
import tempfile
import sys
import re
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description='Constrói lambdas para um ambiente específico')
    parser.add_argument('--env', '-e', default='dev', choices=['dev', 'prod'], help='Ambiente para deployment (dev ou prod)')
    parser.add_argument('lambda_name', nargs='?', help='Nome da lambda para construir (opcional)')
    return parser.parse_args()


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(PROJECT_ROOT, 'shared')
LAMBDAS_DIR = os.path.join(PROJECT_ROOT, 'lambdas')

EXCLUDED_LAMBDAS = ['__pycache__']


def find_requirements_file(folder_path):
    requirements_file = os.path.join(folder_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        return requirements_file
    return None


def install_lambda_optimized_dependencies(requirements_file, target_dir):
    print(f"Instalando dependências otimizadas para Lambda de {requirements_file}...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '-r', requirements_file,
            '--platform', 'manylinux2014_x86_64',
            '--target', target_dir,
            '--only-binary=:all:',
            '--upgrade'
        ], check=True)
        print(f"Dependências instaladas com sucesso em {target_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao instalar dependências: {e}")
        print("Tentando instalação sem otimizações...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                '-r', requirements_file,
                '--target', target_dir,
                '--upgrade'
            ], check=True)
            print("Dependências instaladas com método alternativo")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"ERRO na instalação alternativa: {e2}")
            return False


def adjust_imports(folder_path):
    print(f"Ajustando importações na pasta: {folder_path}")

    patterns = [
        (r'from\s+lambdas\.([^\.]+)\.', r'from '),
        (r'import\s+lambdas\.([^\.]+)\.', r'import ')
    ]

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content
                    for pattern, replacement in patterns:
                        content = re.sub(pattern, replacement, content)

                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  Importações ajustadas em: {os.path.relpath(file_path, folder_path)}")
                except UnicodeDecodeError:
                    print(f"  Erro ao processar {file_path}: não é um arquivo de texto")


def build_lambda(lambda_name, env):
    print(f"\n=== Construindo lambda: {lambda_name} para ambiente: {env} ===")

    if lambda_name in EXCLUDED_LAMBDAS:
        print(f"Lambda {lambda_name} está na lista de exclusão e será ignorada")
        return

    output_dir = os.path.join(PROJECT_ROOT, 'terraform', 'environments', env, 'deployments')

    with tempfile.TemporaryDirectory() as temp_dir:
        lambda_source = os.path.join(LAMBDAS_DIR, lambda_name)

        print(f"Copiando código de {lambda_name}...")
        for item in os.listdir(lambda_source):
            s = os.path.join(lambda_source, item)
            d = os.path.join(temp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        print("Copiando pasta shared como subdiretório...")
        shared_dest = os.path.join(temp_dir, 'shared')
        shutil.copytree(SHARED_DIR, shared_dest)

        print("Ajustando importações...")
        adjust_imports(temp_dir)

        requirements_file = find_requirements_file(lambda_source)
        if requirements_file:
            print(f"Encontrado arquivo de requisitos: {requirements_file}")
            install_lambda_optimized_dependencies(requirements_file, temp_dir)
        else:
            print(f"Nenhum arquivo requirements.txt encontrado para {lambda_name}")

        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f"{lambda_name}.zip")
        print(f"Criando arquivo {output_file}...")

        if os.path.exists(output_file):
            os.remove(output_file)

        shutil.make_archive(
            output_file.replace('.zip', ''),
            'zip',
            temp_dir
        )

        print(f"Lambda construída com sucesso: {output_file}")


if __name__ == "__main__":
    args = parse_arguments()
    env = args.env
    lambda_name = args.lambda_name

    print(f"Ambiente de deployment: {env}")

    lambdas = [d for d in os.listdir(LAMBDAS_DIR) if os.path.isdir(os.path.join(LAMBDAS_DIR, d)) and d not in EXCLUDED_LAMBDAS]

    if lambda_name:
        if lambda_name in EXCLUDED_LAMBDAS:
            print(f"Lambda {lambda_name} está na lista de exclusão e não será construída")
        elif lambda_name in lambdas:
            build_lambda(lambda_name, env)
        else:
            print(f"Lambda não encontrada: {lambda_name}")
    else:
        print(f"Lambdas a serem construídas: {', '.join(lambdas)}")
        for lambda_name in lambdas:
            build_lambda(lambda_name, env)