cd containers
if [ "$1" == "rpi" ];then
    for d in */; do
        dir=${d%/}
        test $(docker run --rm jrcichra/smartcar_$dir_rpi cat commit.txt) = $GITHUB_SHA
    done
else
    for d in */; do
        dir=${d%/}
        test $(docker run --rm jrcichra/smartcar_$dir cat commit.txt) = $GITHUB_SHA
    done
fi