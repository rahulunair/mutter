## Mutter

Mutter is a tool i wrote because there was none to my liking and probably will not be useful to you.

## What it does?

well, the only thing it takes as arguments are 2 docker images, a `base image` and a `final image`, then it extracts the packages and versions
installed in the final image along with the license(fuzzy and terribly in need to refactor this part). This can help when you want to ship an image
and is too lazy to search for all the packages and extract their licenses manually. 


## Usage

```bash
python mutt.py --base_image <image_name> --final_image <image_name>
```

or 

```bash
python mutt.py <base_image> <final_image>
```

It will take a while(it starts up a docker process everytime to grep for licenses per package, I know .. terrible!), please wait and once it's done a **csv** file would be save locally on your computer.

The tool would then scan the **base image** for packages installed along with the dependencies and then diff it with the **final image** and saves the result as a csv. This is done so that only the packages and dependencies installed on the final_image is the one that I care about.



## Which OS is supported?

Supports any host that has a posix shell, but for now only debian based docker images are supported - debian, ubuntu, mint etc..


