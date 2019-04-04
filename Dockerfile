FROM kbase/kb_python:latest

COPY reapNarratives.py /kb/module/

RUN chmod +x /kb/module/reapNarratives.py

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/kbase/narrativeReaper.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="0.0.1" \
      us.kbase.vcs-branch=$BRANCH \
      maintainer="Keith Keller kkeller@lbl.gov"
