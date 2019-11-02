cd containers
for d in */; do
    test $(docker run -it --rm jrcichra/smartcar_$d cat commit.txt) = $TRAVIS_COMMIT
done