package com.neuedu.his.mapper;

import com.neuedu.his.model.vo.MedicalTechTaskVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface MedicalTechWorkMapper {
    List<MedicalTechTaskVO> selectTasks(@Param("registerId") Integer registerId,
                                        @Param("itemType") String itemType,
                                        @Param("state") String state);
}
