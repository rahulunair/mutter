## Mutter

Mutter is a tool i wrote because there was none to my liking and probably will not be useful to you.

## What it does?

well, the only thing it takes as arguments are 2 docker images, a `base image` and a `final image`, then it extracts the packages and versions
installed in the final image along with the license(fuzzy and terribly in need to refactor this part). This can help when you want to ship an image
and is too lazy to search for all the packages and extract their licenses manually. 


## Which OS is supported?

Supports any host that has a posix shell, but for now only debian based docker images are supported - debian, ubuntu, mint etc..


