FROM golang:alpine3.11 as firststage
WORKDIR /smartcar
ADD . .
RUN go build -o controller .
FROM alpine:3.11
WORKDIR /smartcar
COPY --from=firststage /smartcar/controller .
CMD ["./controller"]