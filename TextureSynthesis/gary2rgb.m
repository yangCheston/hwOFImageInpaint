% 读取灰度图像
I = imread('fruits_region_lost.png'); % 请将'yourImage.jpg'替换为您的图像文件名

% 检查I是否已经是彩图，如果是，先转换为灰度图
if size(I,3) == 3
    I = rgb2gray(I);
end

% 将灰度图像复制到三个颜色通道
RGBImage = cat(3, I, I, I);

% 显示结果
subplot(1,2,1);
imshow(I);
title('Original Grayscale Image');

subplot(1,2,2);
imshow(RGBImage);
title('Converted Color Image');

imwrite(RGBImage,'firuits_lost.png');