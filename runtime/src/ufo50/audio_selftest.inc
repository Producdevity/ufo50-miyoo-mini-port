/* Synthetic WAV fixtures exercise the real mixer without a playback device. */
#include "overlay_file_system.h"
int MaAudioSystem_runTests(const char* fixturePath) {
    DataWin data = {0};
    AudioGroup groups[3] = {0};
    Sound sounds[1] = {{.name="synthetic", .audioGroup=2, .audioFile=0,
        .flags=AUDIO_ENTRY_FLAG_IS_EMBEDDED, .volume=1, .pitch=1}};
    data.agrp.count=3; data.agrp.audioGroups=groups;
    data.sond.count=1; data.sond.sounds=sounds;
    data.lazyLoadAudio=true;
    MaAudioSystem* ma=MaAudioSystem_create(&data);
    AudioSystem* audio=(AudioSystem*)ma;
    OverlayFileSystem* fs=OverlayFileSystem_create(fixturePath, fixturePath);
    ma->fileSystem=(FileSystem*)fs;
    arrput(audio->audioGroups, &data);
    ma_engine_config config=ma_engine_config_init();
    config.noDevice=MA_TRUE; config.channels=2; config.sampleRate=44100;
    require(ma_engine_init(&config, &ma->engine)==MA_SUCCESS);
    MaAudioSystem_resetState(ma);
    maGroupLoad(audio, 2);
    require(maGroupIsLoaded(audio, 2) && !maGroupIsLoaded(audio, 1));
    maGroupLoad(audio, 2);
    require(arrlen(audio->audioGroups)==3);
    int32_t sound=maPlaySound(audio, 0, 0, true);
    require(sound>=SOUND_INSTANCE_ID_BASE);
    float pcm[1024]; ma_uint64 read=0;
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read)==MA_SUCCESS && read==512);
    float energy=0; repeat(1024, i) energy+=pcm[i]*pcm[i];
    require(energy>1);
    maSetGroupGain(audio, 2, 0, 100);
    maUpdate(audio, 0.05f); require(fabsf(maGroupGain(ma, 2)-0.5f)<0.001f);
    maUpdate(audio, 0.05f); require(maGroupGain(ma, 2)==0);
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read)==MA_SUCCESS);
    /* Miniaudio ramps volume changes; consume a buffer before checking silence. */
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read)==MA_SUCCESS);
    energy=0; repeat(1024, i) energy+=pcm[i]*pcm[i]; require(energy<0.0001f);
    maGroupUnload(audio, 2);
    require(!maGroupIsLoaded(audio, 2) && !maIsPlaying(audio, sound));
    require(maPlaySound(audio, 0, 0, false)==-1);
    require(maGetSoundLength(audio, 0)==0);
    maDestroy(audio); OverlayFileSystem_destroy(fs);
    logInfo("Audio selftests passed: sparse groups, repeated load, nonzero stereo PCM, group fades, unload safety\n");
    return 0;
}
