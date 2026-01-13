#!/bin/bash
old_branch='sk-daraja-v2'
new_branch='sk-daraja-v3'

git checkout -b $new_branch
git branch -m $old_branch $new_branch
git fetch origin
git branch -u origin/$new_branch $new_branch
git remote set-head origin -a