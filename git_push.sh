git add * -A
git rm -f -r *.pyc *.py~ 
rm *.pyc *.py~ -R
git commit -m "$1 ,automated commit on `date +'%Y-%m-%d %H:%M:%S'`;"
git push origin master