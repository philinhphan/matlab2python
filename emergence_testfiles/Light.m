function [out1] = Light(Col,Percent)

    R = 255*Col(1);
    G = 255*Col(2);
    B = 255*Col(3);
    R = (round((R*Percent/100) + round(255 - Percent/100*255))-1)/255;
    G = (round((G*Percent/100) + round(255 - Percent/100*255))-1)/255;
    B = (round((B*Percent/100) + round(255 - Percent/100*255))-1)/255;
    out1 = [R,G,B];
  
end
