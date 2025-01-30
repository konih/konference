FROM mcr.microsoft.com/azure-functions/python:4-python3.11-core-tools

RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    zsh \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g azure-functions-core-tools@4 --unsafe-perm true
RUN pip install go-task-bin

# Set zsh as default shell
SHELL ["/bin/zsh", "-c"]
RUN chsh -s /bin/zsh

ENV PATH="${PATH}:/root/.local/bin"
