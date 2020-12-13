#!/usr/bin/env bash

rsync -avzhe ssh ucla:/srv/isebel/translations/dan_eng .
rsync -avzhe ssh ucla:/srv/isebel/translations/nld_eng .
rsync -avzhe ssh ucla:/srv/isebel/translations/fry_eng .
rsync -avzhe ssh ucla:/srv/isebel/translations/deu_eng .
