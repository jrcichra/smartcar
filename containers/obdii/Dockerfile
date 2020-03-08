FROM golang:alpine3.11 as firststage
WORKDIR /smartcar_obdii
ADD . .
RUN go build -o smartcar_obdii .
FROM alpine:3.11
WORKDIR /smartcar_obdii
COPY --from=firststage /smartcar_obdii/smartcar_obdii .
CMD ["./smartcar_obdii"]