FROM openjdk:17.0-jdk

COPY ./config.json /code/config.json

COPY ./librespot-api.jar /code/librespot-api.jar

WORKDIR /code

CMD ["java", "-jar", "librespot-api.jar"]

ENTRYPOINT ["java", "-jar", "librespot-api.jar"]
