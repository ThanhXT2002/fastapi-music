from app.internal.utils.youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader()
info = downloader.extract_info('https://www.youtube.com/watch?v=SPTUEeGW50E')

if info:
    formats = info.get('formats', [])
    print(f"Total formats: {len(formats)}")
    
    # Check audio-only formats
    audio_only = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
    print(f"Audio-only formats: {len(audio_only)}")
    
    direct_audio = []
    hls_audio = []
    
    for fmt in audio_only:
        url = fmt.get('url', '')
        is_hls = downloader._is_hls_url(url)
        if is_hls:
            hls_audio.append(fmt)
        else:
            direct_audio.append(fmt)
    
    print(f"\nDirect audio streams: {len(direct_audio)}")
    for i, fmt in enumerate(direct_audio[:3]):
        print(f"  {i+1}. {fmt.get('ext')} - {fmt.get('abr')}kbps")
        print(f"     URL: {fmt.get('url', '')[:100]}...")
    
    print(f"\nHLS audio streams: {len(hls_audio)}")
    for i, fmt in enumerate(hls_audio[:3]):
        print(f"  {i+1}. {fmt.get('ext')} - {fmt.get('abr')}kbps")
        print(f"     URL: {fmt.get('url', '')[:100]}...")
