cd containers
for d in */; do
    dir=${d%/}
    test $(docker run --rm jrcichra/smartcar_$dir cat commit.txt) = $GITHUB_SHA
done