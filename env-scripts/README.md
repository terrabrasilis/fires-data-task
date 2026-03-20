# Environment definition

Set up the environment to run these scripts using docker. See the Dockerfile and the "Runtime Settings" section in the main README file for more details.

To generate the new docker image, use the docker-build.sh script. To avoid overwriting the previous docker image, set a tag version in the git repository before running the build script.

```sh
./docker-build.sh
```

* This script attempts to send the new docker image to the docker's hub registration platform.