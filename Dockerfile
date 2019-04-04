FROM kbase/kb_python:latest

RUN apt-get update && \
    apt-get install -y apt-transport-https software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y docker-ce=18.03.0~ce-0~debian

COPY reapNarratives.py /kb/module/
RUN chmod +x /kb/module/reapNarratives.py

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/kbase/narrativeReaper.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="0.0.1" \
      us.kbase.vcs-branch=$BRANCH \
      maintainer="Keith Keller kkeller@lbl.gov"

ENTRYPOINT [ "/kb/module/reapNarratives.py" ]
