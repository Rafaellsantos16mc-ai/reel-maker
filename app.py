def criar_video(tema, estilo, duracao):
    session_id = str(uuid.uuid4())[:8]
    roteiro = criar_roteiro(
        tema,
        estilo,
        duracao
    )
    links = buscar_imagens(tema)
    caminho_audio = gerar_narracao(
        roteiro,
        session_id
    )
    audio = None
    audio_final = None
    video = None
    clips = []
    audio_cortado = False
    try:
        # =========================
        # CARREGAR NARRAÇÃO
        # =========================
        audio = AudioFileClip(caminho_audio)
        duracao_audio = float(audio.duration)
        # O vídeo terá pelo menos a duração escolhida.
        # Se a narração for maior, acompanha a narração.
        duracao_final = max(
            float(duracao),
            duracao_audio
        )
        # Limite máximo de 5 segundos além da duração escolhida.
        duracao_final = min(
            duracao_final,
            float(duracao) + 5
        )
        # =========================
        # IMAGENS
        # =========================
        quantidade = min(
            len(links),
            5
        )
        duracao_imagem = (
            duracao_final / quantidade
        )
        for i in range(quantidade):
            caminho_img = preparar_imagem(
                links[i],
                session_id,
                i
            )
            clip = ImageClip(
                caminho_img
            ).with_duration(
                duracao_imagem
            )
            clips.append(clip)
        # =========================
        # JUNTAR IMAGENS
        # =========================
        video = concatenate_videoclips(
            clips,
            method="compose"
        )
        # Garante que o vídeo não ultrapasse
        # a duração planejada.
        if video.duration > duracao_final:
            video = video.subclipped(
                0,
                duracao_final
            )
        # =========================
        # AJUSTAR NARRAÇÃO
        # =========================
        if audio.duration > video.duration:
            audio_final = audio.subclipped(
                0,
                video.duration
            )
            audio_cortado = True
        else:
            audio_final = audio
        # =========================
        # COLOCAR NARRAÇÃO
        # =========================
        # Somente a narração.
        # Não existe música de fundo.
        video = video.with_audio(
            audio_final
        )
        # =========================
        # SALVAR MP4
        # =========================
        nome_video = (
            f"reel_{session_id}.mp4"
        )
        caminho_video = os.path.join(
            VIDEOS_DIR,
            nome_video
        )
        video.write_videofile(
            caminho_video,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger=None
        )
        return nome_video, roteiro
    finally:
        # =========================
        # FECHAR VÍDEO
        # =========================
        if video is not None:
            try:
                video.close()
            except Exception:
                pass
        # =========================
        # FECHAR ÁUDIO CORTADO
        # =========================
        if audio_cortado and audio_final is not None:
            try:
                audio_final.close()
            except Exception:
                pass
        # =========================
        # FECHAR ÁUDIO ORIGINAL
        # =========================
        if audio is not None:
            try:
                audio.close()
            except Exception:
                pass
        # =========================
        # FECHAR CLIPS
        # =========================
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        # =========================
        # APAGAR MP3 TEMPORÁRIO
        # =========================
        if os.path.exists(caminho_audio):
            try:
                os.remove(caminho_audio)
            except Exception:
                pass