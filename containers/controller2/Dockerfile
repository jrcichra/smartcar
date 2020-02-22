FROM golang:alpine3.11 as firststage
WORKDIR /smartcar
ADD . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o controller .
FROM alpine:3.11
WORKDIR /smartcar
COPY --from=firststage /smartcar/controller .
CMD ["./controller"]