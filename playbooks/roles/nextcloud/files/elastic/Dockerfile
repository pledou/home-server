FROM elasticsearch:7.6.2

RUN bin/elasticsearch-plugin install --batch ingest-attachment

RUN yum-config-manager --add-repo https://download.opensuse.org/repositories/home:/Alexander_Pozdnyakov/CentOS_7/ && \
    rpm --import https://build.opensuse.org/projects/home:Alexander_Pozdnyakov/public_key && \
    yum update -y && \
    yum install tesseract tesseract-langpack-fra tesseract-langpack-eng  -y && \
    yum clean all

#TODO build RPM for AM64
#TODO upgrade to elastic 7.12.0 and Centos 8