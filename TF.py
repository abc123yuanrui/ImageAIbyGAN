import os, sys
import tensorflow as tf

from DATA import *
from MODEL import *
from FUNCTION import *
from PREPROCESSING import *

print(current_time() + ', exp = %s, load_model path = %s' % (FLAGS['num_exp'], os.path.dirname(os.path.abspath(__file__))))
os.environ["CUDA_VISIBLE_DEVICES"] = FLAGS['num_gpu']
netG_act_o = dict(size=1, index=0)

test_df = DataFlow()
netG = NetInfo('netG-%d' % FLAGS['num_exp'], test_df)
with tf.name_scope(netG.name):
    with tf.variable_scope(netG.variable_scope_name) as scope_full:
        with tf.variable_scope(netG.variable_scope_name + 'A') as scopeA:
            netG_test_output1, netG_test_list = model(netG, test_df.input1, test_df.input2, False, netG_act_o, None, is_first=True)
            netG_test_gfeature1 = netG_test_list[25]
            scopeA.reuse_variables()
            netG_test_dilation_list = []
            for dilation in range(FLAGS['max_dilation']):
                netG_test_dilation_output, _ = model(netG, test_df.input1, test_df.input2, False, netG_act_o, dilation+1)
                netG_test_dilation_list.append(netG_test_dilation_output)


assert len(netG.weights) == len(netG.parameter_names), 'len(weights) != len(parameters)'
saver = tf.train.Saver(var_list=netG.weights, max_to_keep=None)

with tf.name_scope("Resize"):
    tf_input_img_ori = tf.placeholder(tf.uint8, shape=[None, None, 3])
    tf_img_new_h = tf.placeholder(tf.int32)
    tf_img_new_w = tf.placeholder(tf.int32)
    tf_resize_img = tf.image.resize_images(images=tf_input_img_ori, size=[tf_img_new_h, tf_img_new_w], method=tf.image.ResizeMethod.AREA)

sess_config = tf.ConfigProto(log_device_placement=False)
sess_config.gpu_options.allow_growth = True

sess = tf.Session(config=sess_config)
sess.run(tf.global_variables_initializer())
sess.run(tf.local_variables_initializer())
saver.restore(sess, FLAGS['load_model_path_new'])

def checkValidImg(input_img):
    print(current_time() + ', [checkValidImg]')
    if input_img is None:
        print(current_time() + ', img is None')
        return None
    if len(input_img.shape) != 3:
        print(current_time() + ', len(shape) != 3')
        return None
    if input_img.shape[2] != 3:
        print(current_time() + ', shape[2] != 3')
        return None
    if input_img.dtype != np.uint8:
        print(current_time() + ', img.dtype != uint8')
        return None
    return True

def normalizeImage(img, max_length):
    print(current_time() + ', [normalizeImage]')
    [height, width, channels] = img.shape
    print(current_time() + ', original shape = [%d, %d, %d]' % (height, width, channels))
    max_l = max(height, width)

    is_need_resize = max_l != FLAGS['data_image_size']
    if is_need_resize:
        print('need resize!!!')
        use_gpu = False
        if use_gpu and is_downsample:
            # gpu
            new_h, new_w, is_normalize = get_normalize_size_shape_method(img, max_length)
            print('The hight is %s, width becomes %s, is_normalize %s'% new_h,new_w,is_normalize)
            if not is_normalize:
                dict_d = [img, new_h, new_w]
                dict_t = [tf_input_img_ori, tf_img_new_h, tf_img_new_w]
                print(dict_d[1],dict_d[2])
                img = sess.run(tf_resize_img, feed_dict={t:d for t, d in zip(dict_t, dict_d)})
        else:
            # cpu
            img = cpu_normalize_image(img, max_length)
    return img

def getInputPhoto(input_img):
    # print(current_time() + ', [getInputPhoto]: file_name = %s' % (FLAGS['folder_input'] + file_name))
    # file_name_without_ext = os.path.splitext(file_name)[0]
    # input_img = cv2.imread(FLAGS['folder_input'] + file_name, 1)
    #rui#os.remove(FLAGS['folder_input'] + file_name)
    if checkValidImg(input_img):
        h, w, _ = input_img.shape
        #resize_input_img = normalizeImage(input_img, FLAGS['data_max_image_size']) if max(h, w) > FLAGS['data_max_image_size'] else input_img
        resize_input_img = normalizeImage(input_img, FLAGS['data_max_image_size'])
        file_name = file_name_without_ext + FLAGS['data_output_ext']
        #file_name = file_name_without_ext + FLAGS['data_output_ext']
        cv2.imwrite(FLAGS['folder_input'] + file_name, resize_input_img)
        #cv2.imwrite(FLAGS['folder_input'] + file_name_without_ext + '.jpg', resize_input_img)
        #os.rename(FLAGS['folder_input'] + file_name_without_ext + '.jpg', FLAGS['folder_input'] + file_name)
        return file_name
    else:
        return None

def processImg(input_img):
    #print(current_time() + ', [processImg]: file_name = %s' % (FLAGS['folder_input'] + file_in_name))
    # input_img = cv2.imread(FLAGS['folder_input'] + file_in_name, -1)
    resize_input_img = normalizeImage(input_img, FLAGS['data_image_size'])
    resize_input_img, _, _ = random_pad_to_size(resize_input_img, FLAGS['data_image_size'], None, True, False)
    resize_input_img = resize_input_img[None, :, :, :]

    dict_d = [resize_input_img, 1]
    dict_t = [test_df.input1_src, test_df.rate]
    gfeature = sess.run(netG_test_gfeature1, feed_dict={t:d for t, d in zip(dict_t, dict_d)})

    h, w, c = input_img.shape
    rate = int(round(max(h, w) / FLAGS['data_image_size']))
    if rate == 0:
        rate = 1
    padrf = rate * FLAGS['data_padrf_size']
    patch = FLAGS['data_patch_size']
    pad_h = 0 if h % patch == 0 else patch - (h % patch)
    pad_w = 0 if w % patch == 0 else patch - (w % patch)
    pad_h = pad_h + padrf if pad_h < padrf else pad_h
    pad_w = pad_w + padrf if pad_w < padrf else pad_w

    input_img = np.pad(input_img, [(padrf, pad_h), (padrf, pad_w), (0, 0)], 'reflect')
    y_list = []
    for y in range(padrf, h+padrf, patch):
        x_list = []
        for x in range(padrf, w+padrf, patch):
            crop_img = input_img[None, y-padrf:y+padrf+patch, x-padrf:x+padrf+patch, :]
            dict_d = [crop_img, gfeature, rate]
            dict_t = [test_df.input1_src, test_df.input2, test_df.rate]
            #enhance_test_img = sess.run(netG_test_dilation_list[min(9, rate-1)], feed_dict={t:d for t, d in zip(dict_t, dict_d)})
            enhance_test_img = sess.run(netG_test_output1, feed_dict={t:d for t, d in zip(dict_t, dict_d)})
            enhance_test_img = enhance_test_img[0, padrf:-padrf, padrf:-padrf, :]
            x_list.append(enhance_test_img)
        y_list.append(np.concatenate(x_list, axis=1))
    enhance_test_img = np.concatenate(y_list, axis=0)
    enhance_test_img = enhance_test_img[:h, :w, :]
    enhance_test_img = safe_casting(enhance_test_img * tf.as_dtype(FLAGS['data_input_dtype']).max, FLAGS['data_input_dtype'])
    #enhanced_img_file_name = file_out_name_without_ext + FLAGS['data_output_ext']
    #enhance_img_file_path = FLAGS['folder_test_img'] + enhanced_img_file_name
    ##try:
    ##    print(current_time() + ', try remove file path = %s' % enhance_img_file_path)
    ##   os.remove(enhance_img_file_path)
    ##except OSError as e:
    ##    print(current_time() + ', remove fail, error = %s' % e.strerror)
    ##cv2.imwrite(enhance_img_file_path, enhance_test_img)
    #cv2.imwrite(FLAGS['folder_test_img'] + file_out_name_without_ext + '.jpg', enhance_test_img)
    #os.rename(FLAGS['folder_test_img'] + file_out_name_without_ext + '.jpg', enhance_img_file_path)
    #cv2.imwrite(FLAGS['folder_test_img']+ enhanced_img_file_name, enhance_test_img)
    return enhance_test_img
