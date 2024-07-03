FROM harbor.capitalonline.net/base/python:3.7
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com && \
    mkdir /app && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/shanghai" >> /etc/timezone
COPY . /app
WORKDIR /app