# PitchLab for TrueNAS SCALE

PitchLab runs as a Python 3.15 container. It renders General MIDI instruments with FluidSynth and serves each note to the browser as audio. There is no server audio device requirement. Progress stays in the browser's local storage, so it survives container updates but is separate for each browser and domain.

## Install as a TrueNAS Custom App

1. In **Apps**, choose **Discover Apps → more_vert → Install via YAML**.
2. Name the app `pitchlab` and paste the contents of `compose.yaml` into **Custom Config**.
3. Save. When it starts, visit `http://<TrueNAS-LAN-IP>:18473`.
4. In your existing Cloudflared tunnel, point the chosen public hostname to `http://<TrueNAS-LAN-IP>:18473`. If Cloudflared runs on the same host with host networking, `http://127.0.0.1:18473` also works.

The Compose file exposes port 18473 on the NAS. Do not forward that port on your router; let Cloudflared handle external HTTPS. If you want the app restricted to your account, put a Cloudflare Access policy on its public hostname.

## Source and image

The image is built from this folder's `Dockerfile` and published as `ghcr.io/adammoss08/pitchlab:latest`. The SoundFont is installed from Debian's `fluid-soundfont-gm` package during the image build. To build it yourself on a Docker host:

```sh
docker build -t pitchlab:local .
docker run --rm -p 18473:8080 pitchlab:local
```

The app does not need a data mount. It asks for note names, not octaves or microphone singing input.
