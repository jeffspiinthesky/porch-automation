FROM ubuntu:24.04

RUN apt update
RUN apt upgrade -y
RUN apt install -y python3 python3-pip python3-venv libssl-dev

WORKDIR /
RUN python3 -m venv venv
ADD requirements.txt /requirements.txt
RUN /venv/bin/pip3 install -r requirements.txt
RUN ln -sf /usr/lib/aarch64-linux-gnu/libcrypto.so.3 /usr/lib/libcrypto.so.3
RUN ln -sf /usr/lib/aarch64-linux-gnu/libssl.so.3 /usr/lib/libssl.so.3
ADD patch.py /patch.py
RUN /venv/bin/python3 /patch.py

ADD alexa_skill.py /alexa_skill.py

ENTRYPOINT ["/venv/bin/python3", "alexa_skill.py"]
