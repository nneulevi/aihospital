package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiImageFile;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface AiImageFileMapper {

    @Insert("INSERT INTO ai_image_file(check_request_id, register_id, file_path, file_name, file_size, file_format, upload_time, upload_by) " +
            "VALUES(#{checkRequestId}, #{registerId}, #{filePath}, #{fileName}, #{fileSize}, #{fileFormat}, NOW(), #{uploadBy})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiImageFile aiImageFile);

    @Select("SELECT * FROM ai_image_file WHERE id = #{id}")
    AiImageFile selectById(Integer id);

    @Select("SELECT * FROM ai_image_file WHERE check_request_id = #{checkRequestId}")
    List<AiImageFile> selectByCheckRequestId(Integer checkRequestId);

    @Select("SELECT * FROM ai_image_file WHERE register_id = #{registerId}")
    List<AiImageFile> selectByRegisterId(Integer registerId);
}