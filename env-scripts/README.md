# Environment definition

Set the environment to run these scripts using the docker. See Dockerfile for more details.

To generate the new docker image, use the docker-build.sh script after setting the version of your image in the PROJECT_VERSION file.

```sh
./docker-build.sh
```

* This script attempts to send the new docker image to the docker's hub registration platform.