#!/bin/bash

# Navigate to the directory containing your local Git repository
cd "$(dirname "$0")"

# Load variables while ignoring lines starting with '#' and empty lines
while IFS= read -r line; do
  if [[ "$line" =~ ^[^#]*= ]] && [[ ! "$line" =~ ^[[:space:]]*# ]]; then
    export "$line"
  fi
done < .env

# move to primary dir
#cd ..

# Read user input
read -p "what change are we making today: " modification

# produce tree of project
#tree > tree

# save latest dependencies
#pip freeze > requirements.txt

#initialize branch name 
branch='main'

#initialize repo
# git init

# Create a new branch named 'rag'
# git checkout -b $branch

# Add all changes to the Git staging are
git add .

# for pushing large files such as the models
#git lfs track "rag_models/*" "data/*" 
#git lfs push --all origin $branch

#check status of files to be committed
git status

# Commit the changes with a descriptive message
git commit -m "$modification"

# git branch -M $branch

# git remote add origin https://$GIT_PAT@github.com/kuriofoolio/scrabble_kenya_payments_system.git
# git remote add origin https://github.com/kuriofoolio/scrabble_kenya_payments_system.git

#Push the changes to your GitHub repository
git push -u origin $branch

# to overwrite all changes on the branch
# git push --force origin $branch
