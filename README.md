# Flocrypt

Flocrypt é um aplicativo desktop para criptografar e descriptografar arquivos localmente. Ele possui uma interface gráfica escura, suporte a seleção tradicional de arquivos e arrastar-e-soltar, histórico dos arquivos processados e geração de arquivos protegidos com a extensão `.floki`.

O processamento acontece no próprio computador. Os arquivos e senhas não são enviados para servidores ou serviços externos.

## Interface

![Interface do Flocrypt](tela.png)

## Principais recursos

- Criptografia e descriptografia de arquivos de qualquer formato.
- AES-256-GCM, com autenticação de integridade.
- Derivação de chave com PBKDF2-HMAC-SHA512.
- Salt aleatório de 16 bytes para cada operação.
- Nonce aleatório de 12 bytes para cada operação AES-GCM.
- Seleção de arquivo por diálogo ou arrastar-e-soltar.
- Arquivos criptografados com extensão `.floki`.
- Histórico local com filtro por arquivos criptografados e descriptografados.
- Seleção de um arquivo diretamente pelo histórico.
- Remoção individual de registros do histórico.
- Limpeza segura do arquivo original após uma transformação concluída.
- Interface com mensagens de sucesso, aviso e erro integradas ao visual do aplicativo.

## O que é criptografado

Ao criptografar um arquivo, o Flocrypt:

1. Lê o conteúdo do arquivo escolhido.
2. Gera um salt aleatório.
3. Deriva uma chave de 256 bits a partir da senha informada.
4. Gera um nonce aleatório para o AES-GCM.
5. Inclui no pacote o nome original do arquivo e o conteúdo original.
6. Criptografa e autentica esse conjunto com AES-256-GCM.
7. Salva o resultado como:

```text
nome-do-arquivo.extensao.floki
```

O arquivo `.floki` contém o identificador do formato, o salt, o nonce e o conteúdo autenticado. A senha não é armazenada.

## Estrutura de proteção

### AES-256-GCM

O AES-GCM oferece duas propriedades importantes:

- Confidencialidade: o conteúdo não pode ser lido sem a chave correta.
- Integridade e autenticidade: alterações no arquivo ou uma senha incorreta fazem a descriptografia falhar.

Se o conteúdo autenticado não for válido, o aplicativo informa que a senha pode estar incorreta ou que o arquivo foi corrompido.

### PBKDF2-HMAC-SHA512

A senha do usuário não é usada diretamente como chave. O Flocrypt utiliza PBKDF2 com SHA-512, 600.000 iterações, salt aleatório e uma chave final de 32 bytes. Isso torna ataques de tentativa de senha mais caros.

### Limpeza do arquivo original

Depois que a criptografia ou descriptografia termina com sucesso, o arquivo original é sobrescrito com dados aleatórios em três passadas e removido.

Essa limpeza reduz a recuperação simples do arquivo original, mas não deve ser considerada uma garantia absoluta contra ferramentas forenses, cópias de segurança, snapshots, sistemas de arquivos modernos ou SSDs com nivelamento de desgaste.

## Quando utilizar

O Flocrypt pode ser usado para:

- Proteger documentos pessoais antes de armazená-los.
- Guardar cópias de contratos, relatórios e documentos financeiros.
- Proteger backups locais.
- Transportar arquivos em um pendrive ou disco externo.
- Armazenar arquivos sensíveis em pastas compartilhadas.
- Criar uma camada adicional de proteção antes de enviar um arquivo por outro canal.

Ele é especialmente útil quando você precisa de uma proteção local simples e não quer depender de uma conta ou serviço de nuvem.

## Quando não utilizar sozinho

O Flocrypt não substitui:

- Backup em locais diferentes.
- Antivírus e proteção do sistema operacional.
- Criptografia completa do disco.
- Controle de acesso de usuários.
- Gerenciadores de senha.
- Políticas corporativas de retenção e auditoria.

O arquivo protegido depende da senha. Se ela for perdida, não existe mecanismo de recuperação implementado.

## Requisitos

- Python 3.10 ou superior recomendado.
- Windows 10/11 ou uma distribuição Linux com Tk disponível.
- Ambiente virtual recomendado.
- Dependências listadas em `requirements.txt`.

As principais bibliotecas são:

- `customtkinter`: interface gráfica.
- `cryptography`: AES-GCM, PBKDF2 e primitivas criptográficas.
- `tkinterdnd2`: suporte a arrastar-e-soltar.
- `pyinstaller`: geração de executável.

## Instalação no Linux

### 1. Instalar o Python e o Tk

Em distribuições baseadas em Debian ou Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-tk
```

### 2. Criar e ativar o ambiente virtual

Na pasta do projeto:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Executar

```bash
python main.py
```

Para sair do ambiente virtual:

```bash
deactivate
```

## Instalação no Windows

### 1. Instalar o Python

Instale o Python pelo site oficial ou pela Microsoft Store. Durante a instalação pelo instalador tradicional, marque a opção **Add Python to PATH**.

Confirme no PowerShell:

```powershell
py --version
```

### 2. Criar e ativar o ambiente virtual

Na pasta do projeto:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação de scripts, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois ative novamente:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Executar

```powershell
python main.py
```

Para sair do ambiente virtual:

```powershell
deactivate
```

## Como utilizar

### Criptografar um arquivo

1. Abra o Flocrypt.
2. Clique na área de seleção ou arraste um arquivo para a dropzone.
3. Digite uma senha forte.
4. Clique em **Criptografar**.
5. O arquivo `.floki` será criado na mesma pasta do arquivo original.
6. Após o sucesso, o original será removido usando o procedimento de limpeza segura do aplicativo.

### Descriptografar um arquivo

1. Selecione um arquivo `.floki`.
2. Digite a senha usada na criptografia.
3. Clique em **Descriptografar**.
4. O arquivo original será recriado na mesma pasta.
5. Após o sucesso, o arquivo `.floki` será removido pelo procedimento de limpeza segura.

### Usar o histórico

- Clique em um registro para selecionar o arquivo associado.
- Use as abas para filtrar criptografados ou descriptografados.
- Passe o mouse sobre um item para destacá-lo.
- Use o botão de lixeira para remover o registro do histórico.
- A rolagem do histórico continua disponível pela roda do mouse, mesmo com a barra visual oculta.

O histórico é salvo localmente em:

```text
Linux:   ~/.cipherdrop_historico.json
Windows: %USERPROFILE%\\.cipherdrop_historico.json
```

O histórico guarda metadados como nome, tamanho, data, tipo e caminho do arquivo. Ele não guarda a senha nem o conteúdo criptografado.

## Gerar um executável

O projeto usa PyInstaller para empacotar o aplicativo sem abrir um console.

### Linux

Com o ambiente virtual ativado:

```bash
python -m PyInstaller --noconfirm --onefile --windowed \
  --collect-all customtkinter \
  --collect-all tkinterdnd2 \
  --name Flocrypt main.py
```

O executável será criado em:

```text
dist/Flocrypt
```

Execute com:

```bash
./dist/Flocrypt
```

### Windows

Com o ambiente virtual ativado:

```powershell
python -m PyInstaller --noconfirm --onefile --windowed `
  --collect-all customtkinter `
  --collect-all tkinterdnd2 `
  --name Flocrypt main.py
```

O executável será criado em:

```text
dist\\Flocrypt.exe
```

O executável deve ser gerado no mesmo sistema operacional em que será utilizado. Para distribuir uma versão Windows, gere o executável no Windows; para distribuir uma versão Linux, gere-o no Linux.

## Boas práticas de segurança

- Use uma senha longa, exclusiva e difícil de adivinhar.
- Não reutilize a senha em outros serviços.
- Armazene a senha em um gerenciador de senhas.
- Teste a descriptografia antes de apagar cópias importantes.
- Mantenha backups independentes dos arquivos importantes.
- Não compartilhe a senha junto com o arquivo `.floki`.
- Evite colocar a senha em scripts, histórico do terminal ou arquivos de configuração.
- Lembre-se de que a perda da senha significa perda prática do acesso ao conteúdo.

## Limitações atuais

- Não existe recuperação de senha.
- O histórico é local e não é sincronizado entre computadores.
- O aplicativo não oferece compartilhamento, nuvem ou servidor remoto.
- O procedimento de sobrescrita não garante eliminação forense em todos os tipos de armazenamento.
- O nome original é armazenado dentro do pacote criptografado para permitir a restauração automática.
- A extensão `.floki` identifica a convenção do aplicativo, mas a validação real do conteúdo é feita pelo cabeçalho interno e pela autenticação AES-GCM.

## Licença

Este projeto ainda não define uma licença no repositório. Não redistribua ou incorpore o código em outro produto sem estabelecer previamente os termos de uso.
