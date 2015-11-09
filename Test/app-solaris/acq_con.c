#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <time.h>
#include <redpitaya/rp.h>

int stop = 0;
FILE* time_stamps_file;
FILE* data_file;

void saveTimeStamp(int sig);
void quitHandler(int sig){ stop = 1; }
void openTimeStampsFile(){	time_stamps_file = fopen("/tmp/time_stamps", "ab"); }
void closeTimeStampsFile(){	fclose(time_stamps_file); }
void saveBuffToFile(float * buffer, uint32_t size);
void openBuffFile();
void closeBuffFile();

void cleanUpResources(float* buff) {
	/* Releasing resources */
	free(buff);
	rp_Release();
	closeTimeStampsFile();
}

void initRedPitaya() {
	/* Print error, if rp_Init() function failed */
	if (rp_Init() != RP_OK) {
		fprintf(stderr, "Rp api init failed!n");
	}
}

void defineSignals() {
	signal(SIGTERM, quitHandler);
	signal(SIGINT, saveTimeStamp);
}

int main(int argc, char **argv){
	int stop = 0;
    uint32_t array_size = 16 * 1024; //Current buffer size.

	defineSignals();
	openTimeStampsFile();
	openBuffFile();
	initRedPitaya();

    /* mount sd-card in rw mode */
    system("rw");
    /* allocate memory buffer */
    float *buff = (float *)malloc(array_size * sizeof(float));
 
    /* Starts acquisition */
    rp_AcqStart();
    rp_AcqSetTriggerSrc(RP_TRIG_SRC_DISABLED);

	printf("starting ! ! !\n");
	fflush(stdout);

	/* acquire till stop */
    while(!stop){
	    /* Get the whole buffer into buf */
    	raise(SIGINT);
    	rp_AcqGetOldestDataV(RP_CH_1, &array_size, buff);
	    saveBuffToFile(buff, array_size);
    }
    printf("stop ! ! !");
	fflush(stdout);

	cleanUpResources(buff);
    return 0;
}

void saveTimeStamp(int sig)
{
	/* Time struct used for experiments */
	static struct timespec last_time;
	long long time_stamp;
	struct timespec curr_time;
	clock_gettime(CLOCK_REALTIME, &curr_time);
	time_stamp = (curr_time.tv_sec - last_time.tv_sec)*1000000000 + ((curr_time.tv_nsec - last_time.tv_nsec));
	fprintf(time_stamps_file, "%lld, \n", time_stamp);
	last_time = curr_time;
}

void saveBuffToFile(float *buffer, uint32_t size)
{
	for(int i = 0; i < size; i++) fprintf(data_file, "%f,\n", buffer[i]);
	//fwrite(buffer, sizeof(float), sizeof(buffer), data_file);
}

void openBuffFile()
{
	data_file = fopen("/opt/data.txt", "ab+");
	if(data_file != NULL)printf("File opened!\n");
}

void closeBuffFile()
{
	fclose(data_file);
}



